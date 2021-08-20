# pylint: skip-file
# type: ignore

import sys

sys.path.append("C:\\Users\\parad\\OneDrive\\Desktop\\pytrnsys\\pytrnsys")
import pytrnsys.rsim.runParallelTrnsys as runTrnsys
import pytrnsys.psim.processParallelTrnsys as processTrnsys

import os


class ProcessMain:
    def processAction(self, logger, path):
        pathConfig = path
        configFile = "process.config"
        processTool = processTrnsys.ProcessParallelTrnsys()

        fullPath = os.path.join(path, configFile)
        logger.info("Starting ProcessParallelTrnsys with " + fullPath)

        try:
            processTool.readConfig(pathConfig, configFile)
        except ValueError as e:
            logger.error("EXCEPTION WHILE TRYING TO EXECUTE ProcessParallelTrnsys.readConfig")
            errorStatement = ""
            for words in e.args:
                errorStatement += str(words)
            return True, errorStatement
        except OSError as e:
            logger.error("EXCEPTION WHILE TRYING TO EXECUTE ProcessParallelTrnsys.readConfig")
            return True, str(e)
        except:
            logger.error("UNDEFINED EXCEPTION WHILE TRYING TO EXECUTE ProcessParallelTrnsys.readConfig")
            return True, ""

        try:
            processTool.process()
            logger.info("Successfully executed ProcessParallelTrnsys with " + fullPath)
            return False, ""
        except ValueError as e:
            logger.error("EXCEPTION WHILE TRYING TO EXECUTE ProcessParallelTrnsys.process")
            errorStatement = ""
            for words in e.args:
                errorStatement += str(words)
            return True, errorStatement
        except OSError as e:
            logger.error("EXCEPTION WHILE TRYING TO EXECUTE ProcessParallelTrnsys.process")
            return True, str(e)
        except:
            logger.error("UNDEFINED EXCEPTION WHILE TRYING TO EXECUTE ProcessParallelTrnsys.process")
            return True, ""
