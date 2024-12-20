import subprocess, logging, argparse, re, zipfile, os
from typing import List
from datetime import datetime

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start an executable with given arguments.")
    parser.add_argument("--powerDocuPath", type=str, required=True, help="Path to the PowerDocu executable")
    parser.add_argument("--solutionPath", type=str, required=True, help="Path to the solution file that should be documented")
    parser.add_argument("--documentationOutputPath", type=str, required=True, help="Path where the generated documentation should be saved")
    try:
        return parser.parse_args()
    except argparse.ArgumentTypeError as e:
        logging.error(f"An error occurred while parsing the arguments: {e}")
        raise
    except SystemExit as e:
        logging.error(f"An error occurred while parsing the arguments: {e}")
        parser.print_help()
        raise

def start_exe(path: str, args: str) -> None:
    try:
        command = ["powershell", f"Start-Process \"{path}\" -ArgumentList {args} -Wait"]
        subprocess.run(command, check=True)
        logging.info(f"Successfully started {path} with arguments {args}")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while starting the executable: {e}")

def remove_guids_from_solution(solutionPath: str) -> str:
    filePattern = re.compile(r"-?.{8}-.{4}-.{4}-.{4}-.{12}")
    xmlPattern = re.compile(r".{8}-.{4}-.{4}-.{4}-.{12}")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    outputFileDirectory: str = f"temp\\{timestamp}"
    outputFilePath: str = f"{outputFileDirectory}\\cleanedSolution.zip"

    os.makedirs(outputFileDirectory, exist_ok=True)
    logging.info(f"Created temporary directory: {outputFileDirectory}")

    try:
        with zipfile.ZipFile(solutionPath, 'r') as zip_ref:
            zip_ref.extractall(outputFileDirectory)
            logging.info(f"Extracted {solutionPath} to {outputFileDirectory}")
    except zipfile.BadZipFile as e:
        logging.error(f"Failed to extract {solutionPath}: {e}")
        raise

    for root, dirs, files in os.walk(outputFileDirectory):
        for file in files:
            filePath = os.path.join(root, file)
            newFileName = filePattern.sub('', file)
            newFilePath = os.path.join(root, newFileName)

            try:
                os.rename(filePath, newFilePath)
                logging.info(f"Renamed {filePath} to {newFilePath}")
            except OSError as e:
                logging.error(f"Failed to rename {filePath} to {newFilePath}: {e}")
                raise

            if newFileName.endswith('.xml'):
                try:
                    with open(newFilePath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    newContent = xmlPattern.sub('', content)
                    with open(newFilePath, 'w', encoding='utf-8') as f:
                        f.write(newContent)
                    logging.info(f"Processed XML file: {newFilePath}")
                except IOError as e:
                    logging.error(f"Failed to process XML file {newFilePath}: {e}")
                    raise

    try:
        with zipfile.ZipFile(outputFilePath, 'w') as zip_ref:
            for root, dirs, files in os.walk(outputFileDirectory):
                for file in files:
                    filePath = os.path.join(root, file)
                    if file != "cleanedSolution.zip":  
                        arcname = os.path.relpath(filePath, outputFileDirectory)
                        zip_ref.write(filePath, arcname)
            logging.info(f"Created cleaned solution zip: {outputFilePath}")
    except IOError as e:
        logging.error(f"Failed to create zip file {outputFilePath}: {e}")
        raise

    for root, dirs, files in os.walk(outputFileDirectory):
        for file in files:
            filePath = os.path.join(root, file)
            if file != "cleanedSolution.zip":
                try:
                    os.remove(filePath)
                    logging.info(f"Removed temporary file: {filePath}")
                except OSError as e:
                    logging.error(f"Failed to remove temporary file {filePath}: {e}")
                    raise

    for root, dirs, files in os.walk(outputFileDirectory, topdown=False):
        for dir in dirs:
            dirPath = os.path.join(root, dir)
            try:
                os.rmdir(dirPath)
                logging.info(f"Removed temporary directory: {dirPath}")
            except OSError as e:
                logging.error(f"Failed to remove temporary directory {dirPath}: {e}")
                raise

    return outputFilePath

def main() -> None:
# setup
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    args = parse_arguments()
    powerDocuPath:str = args.powerDocuPath
    solutionPath:str = args.solutionPath
    documentationOutputPath:str = args.documentationOutputPath
# remove the guids from the solution
    cleanedSolutionPath:str = remove_guids_from_solution(solutionPath)
    cleanedSolutionPath = "C:\\Users\\FabianPfriem\\PipelineAutomation\\" + cleanedSolutionPath
# run powerDocu
    start_exe(powerDocuPath, f"\"-p {cleanedSolutionPath}\", \"-m\", \"-o {documentationOutputPath}\"")



if __name__ == "__main__":
    main()

