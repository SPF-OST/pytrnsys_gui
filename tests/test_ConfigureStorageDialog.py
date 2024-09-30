import pytest as _pt
import unittest as _ut

import trnsysGUI.project as prj


def _createMainWindow(projectFolder, projectName, qtbot):
    """ This might fit well as a helper class.
        At the moment it is unclear whether this is generic enough for that.
    """
    projectJsonFilePath = projectFolder / f"{projectName}.json"
    project = prj.LoadProject(projectJsonFilePath)

    logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

    mainWindow = _mw.MainWindow(logger, project)  # type: ignore[attr-defined]

    qtbot.addWidget(mainWindow)
    mainWindow.showBoxOnClose = False
    mainWindow.editor.forceOverwrite = True

    return mainWindow


@_pt.mark.skip(reason='Incomplete tests')
class TestConfigureStorageDialog(_ut.TestCase):
    def setUp(self, qtbot):
        self.qtbot = qtbot
        self.maxDiff = None

    def test__load_heat_exchangers(self, qtbot):
        assert False

    def test__get_heat_exchanger_list_item_text(self, qtbot):
        assert False

    def test__load_direct_port_pairs(self, qtbot):
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
