import pytest as _pt
import unittest as _ut
import pathlib as _pl
import collections.abc as _abc

import PyQt5.QtCore as _core

import pytrnsys.utils.log as _ulog

import trnsysGUI.project as prj
import trnsysGUI.mainWindow as mw
import trnsysGUI.blockItemHasInternalPiping as bip
import trnsysGUI.storageTank.widget as stw
import trnsysGUI.names.rename as rename


_CURRENT_DIR = _pl.Path(__file__).parent
_PROJECT_DIR = _CURRENT_DIR / ".." / "data" / "diagramForConfigStorageDialog"
_PROJECT_NAME = "diagramForConfigStorageDialog"


def _createMainWindow(projectFolder, projectName, qtbot):
    """ This might fit well as a helper class.
        At the moment it is unclear whether this is generic enough for that.
    """
    # TODO: add window to qtbot automatically
    projectJsonFilePath = projectFolder / f"{projectName}.json"
    project = prj.LoadProject(projectJsonFilePath)

    logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

    mainWindow = mw.MainWindow(logger, project)  # type: ignore[attr-defined]

    qtbot.addWidget(mainWindow)
    mainWindow.showBoxOnClose = False
    mainWindow.editor.forceOverwrite = True

    return mainWindow


def get_object_from_list(trnsysObjs: _abc.Sequence[bip.BlockItemHasInternalPiping],
                         desiredBlockItem: bip.BlockItemHasInternalPiping):
    """ Currently returns only one. """
    for trnsysObj in trnsysObjs:
        if isinstance(trnsysObj, desiredBlockItem):
            return trnsysObj


# @_pt.mark.skip(reason='Incomplete tests')
class TestConfigureStorageDialog:
    # TODO: ensure popup window does not show up.

    def test__open_dialog_when_dbl_click(self, qtbot):
        mainWindow = _createMainWindow(_PROJECT_DIR, _PROJECT_NAME, qtbot)
        qtbot.addWidget(mainWindow)
        storageTank = get_object_from_list(mainWindow.editor.trnsysObj, stw.StorageTank)
        storageTank.mouseDoubleClickEvent(_core.QEvent.MouseButtonDblClick)

        # TODO: assert dialog opened.

        assert False

    def test__load_heat_exchangers(self, qtbot):
        """ Is called when project is opened with existing storage tanks.
        Also called when a new heat exchanger is added to a storage tank via _addHeatExchanger method.
        """
        # TODO: mock editor,
        # TODO: prep renameHelper,
        # TODO: Mock storage tank,
        # TODO: assert
        storageTank = mock
        editor = mock
        renameHelper = mock




        qtbot.addWidget(ConfigureStorageDialog(self, self.editor, renameHelper, self.editor.projectFolder))



        assert False

    def test__get_heat_exchanger_list_item_text(self, qtbot):
        """ Static method to get the name of the heat exchanger.
        """
        assert False

    def test__load_direct_port_pairs(self, qtbot):
        """ Called when a project is opened with existing direct port pairs.
        Called when a new direct port pair is added to the storage tank via addPortPair method
        """
        assert False

    def test__get_direct_port_pair_list_item_text(self, qtbot):
        assert False

    def test_list_wlclicked(self, qtbot):
        assert False

    def test_list_wrclicked(self, qtbot):
        assert False

    def test_list_wl2clicked(self, qtbot):
        assert False

    def test_list_wr2clicked(self, qtbot):
        assert False

    def test_add_hx(self, qtbot):
        assert False

    def test_min_offset_distance(self, qtbot):
        assert False

    def test_offsets_in_range(self, qtbot):
        assert False

    def test__add_hx_l(self, qtbot):
        assert False

    def test__add_hx_r(self, qtbot):
        assert False

    def test__add_heat_exchanger(self, qtbot):
        assert False

    def test_add_port_pair(self, qtbot):
        assert False

    def test_remove_port_pair_left(self, qtbot):
        assert False

    def test_remove_port_pair_right(self, qtbot):
        assert False

    def test__remove_selected_port_pairs(self, qtbot):
        assert False

    def test_remove_hx_l(self, qtbot):
        assert False

    def test_remove_hx_r(self, qtbot):
        assert False

    def test__remove_selected_heat_exchangers(self, qtbot):
        assert False

    def test__remove_ports(self, qtbot):
        assert False

    def test__remove_connection_if_any(self, qtbot):
        assert False

    def test_modify_hx(self, qtbot):
        assert False

    def test__get_first_selected_item_and_heat_exchanger(self, qtbot):
        assert False

    def test_modify_port(self, qtbot):
        assert False

    def test__get_first_selected_direct_port_pair_list_widget_item(self, qtbot):
        assert False

    def test_incr_size(self, qtbot):
        assert False

    def test_decr_size(self, qtbot):
        assert False

    def test__change_size(self, qtbot):
        assert False

    def test_cancel(self, qtbot):
        assert False
