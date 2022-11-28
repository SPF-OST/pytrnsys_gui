# pylint: skip-file
# type: ignore

import os

import pytrnsys.psim.processParallelTrnsys as _ppt

import pytrnsys.utils.result as _res


class ProcessMain:
    def processAction(self, logger, path) -> _res.Result[None]:
        pathConfig = path
        configFile = "process.config"
        processTool = _ppt.ProcessParallelTrnsys()

        fullPath = os.path.join(path, configFile)
        logger.info("Starting ProcessParallelTrnsys with " + fullPath)

        try:
            processTool.readConfig(pathConfig, configFile)
        except Exception as e:
            return _res.Error(f"An error occurred reading the file {configFile} at {pathConfig}: {repr(e)}")
        except:
            return _res.Error(f"An undefined error occurred reading the file {configFile} at {pathConfig}.")

        try:
            processTool.process()
            logger.info("Successfully executed ProcessParallelTrnsys with %s", fullPath)
            return None
        except Exception as e:
            return _res.Error(f"An error occurred processing the file {configFile} at {pathConfig}: {repr(e)}")
        except:
            return _res.Error(f"An undefined error occurred processing the file {configFile} at {pathConfig}.")
