import builtins
import importlib

import pytest
from unittest import mock

from sonic_platform_base import chassis_base
from sonic_platform_base.chassis_base import ChassisBase

class TestChassisBase:

    def test_reboot_cause(self):
        chassis = ChassisBase()
        assert(chassis.REBOOT_CAUSE_POWER_LOSS == "Power Loss")
        assert(chassis.REBOOT_CAUSE_THERMAL_OVERLOAD_CPU == "Thermal Overload: CPU")
        assert(chassis.REBOOT_CAUSE_THERMAL_OVERLOAD_ASIC == "Thermal Overload: ASIC")
        assert(chassis.REBOOT_CAUSE_THERMAL_OVERLOAD_OTHER == "Thermal Overload: Other")
        assert(chassis.REBOOT_CAUSE_INSUFFICIENT_FAN_SPEED == "Insufficient Fan Speed")
        assert(chassis.REBOOT_CAUSE_WATCHDOG == "Watchdog")
        assert(chassis.REBOOT_CAUSE_HARDWARE_OTHER == "Hardware - Other")
        assert(chassis.REBOOT_CAUSE_HARDWARE_BIOS == "BIOS")
        assert(chassis.REBOOT_CAUSE_HARDWARE_CPU == "CPU")
        assert(chassis.REBOOT_CAUSE_HARDWARE_BUTTON == "Push button")
        assert(chassis.REBOOT_CAUSE_HARDWARE_RESET_FROM_ASIC == "Reset from ASIC")
        assert(chassis.REBOOT_CAUSE_NON_HARDWARE == "Non-Hardware")

    def test_chassis_base(self):
        chassis = ChassisBase()
        not_implemented_methods = [
                [chassis.get_uid_led, [], {}],
                [chassis.set_uid_led, ["COLOR"], {}],
                [chassis.get_dpu_id, [], {"name": "DPU0"}],
                [chassis.get_dataplane_state, [], {}],
                [chassis.get_controlplane_state, [], {}],
            ]

        for method in not_implemented_methods:
            exception_raised = False
            try:
                func = method[0]
                args = method[1]
                kwargs = method[2]
                func(*args, **kwargs)
            except NotImplementedError:
                exception_raised = True

            assert exception_raised

    @mock.patch('sonic_py_common.device_info.is_switch_bmc', return_value=True)
    def test_system_led_bmc(self, _mock_is_switch_bmc):
        # BMC platforms have no controllable system LED, so the base class
        # provides no-op defaults instead of raising NotImplementedError.
        chassis = ChassisBase()
        assert(chassis.initizalize_system_led() == True)
        assert(chassis.set_status_led("green") == False)
        assert(chassis.get_status_led() == "N/A")

    @mock.patch.object(chassis_base, 'device_info', None)
    def test_system_led_no_device_info(self):
        # chassis_base tolerates device_info being None when sonic_py_common is
        # shadowed by a partial mock. These methods must still raise
        # NotImplementedError rather than AttributeError in that case.
        chassis = ChassisBase()
        not_implemented_methods = [
                [chassis.initizalize_system_led, [], {}],
                [chassis.set_status_led, ["COLOR"], {}],
                [chassis.get_status_led, [], {}],
            ]

        for method in not_implemented_methods:
            exception_raised = False
            try:
                func = method[0]
                args = method[1]
                kwargs = method[2]
                func(*args, **kwargs)
            except NotImplementedError:
                exception_raised = True

            assert exception_raised

    @mock.patch('sonic_py_common.device_info.is_switch_bmc', return_value=False)
    def test_system_led_non_bmc(self, _mock_is_switch_bmc):
        # Non-BMC platforms are expected to implement these themselves.
        chassis = ChassisBase()
        not_implemented_methods = [
                [chassis.initizalize_system_led, [], {}],
                [chassis.set_status_led, ["COLOR"], {}],
                [chassis.get_status_led, [], {}],
            ]

        for method in not_implemented_methods:
            exception_raised = False
            try:
                func = method[0]
                args = method[1]
                kwargs = method[2]
                func(*args, **kwargs)
            except NotImplementedError:
                exception_raised = True

            assert exception_raised

    def test_smartswitch(self):
        chassis = ChassisBase()
        assert(chassis.is_smartswitch() == False)
        assert(chassis.is_dpu() == False)

    def test_sensors(self):
        chassis = ChassisBase()
        assert(chassis.get_num_voltage_sensors() == 0)
        assert(chassis.get_all_voltage_sensors() == [])
        assert(chassis.get_voltage_sensor(0) == None)
        chassis._voltage_sensor_list = ["s1"]
        assert(chassis.get_all_voltage_sensors() == ["s1"])
        assert(chassis.get_voltage_sensor(0) == "s1")
        assert(chassis.get_num_current_sensors() == 0)
        assert(chassis.get_all_current_sensors() == [])
        assert(chassis.get_current_sensor(0) == None)
        chassis._current_sensor_list = ["s1"]
        assert(chassis.get_all_current_sensors() == ["s1"])
        assert(chassis.get_current_sensor(0) == "s1")

    def test_get_bmc(self):
        chassis = ChassisBase()
        assert(chassis.get_bmc() == None)
        mock_bmc = "mock_bmc_instance"
        chassis._bmc = mock_bmc
        assert(chassis.get_bmc() == mock_bmc)

    def test_get_sed_mgmt(self):
        chassis = ChassisBase()
        assert(chassis.get_sed_mgmt() == None)
        mock_sed_mgmt = "mock_sed_mgmt_instance"
        chassis._sed_mgmt = mock_sed_mgmt
        assert(chassis.get_sed_mgmt() == mock_sed_mgmt)

    def test_is_bmc(self):
        chassis = ChassisBase()
        assert chassis.is_bmc() is False

        class BmcChassis(ChassisBase):
            def is_bmc(self):
                return True

        bmc = BmcChassis()
        assert bmc.is_bmc() is True

    def test_is_liquid_cooled(self):
        chassis = ChassisBase()
        assert chassis.is_liquid_cooled() is False

        class LiquidCooledChassis(ChassisBase):
            def is_liquid_cooled(self):
                return True

        liquid = LiquidCooledChassis()
        assert liquid.is_liquid_cooled() is True

    def test_get_liquid_cooling(self):
        chassis = ChassisBase()
        assert chassis.get_liquid_cooling() is NotImplementedError

    def test_switch_host_module_at_index_zero(self):
        '''
        On a BMC chassis, only the Switch-Host is modelled as a module.
        get_all_modules() returns [switch_host] and index 0 fetches it.
        get_module_index() maps the Switch-Host name back to index 0.
        '''
        from sonic_platform_base.module_base import ModuleBase

        class SwitchHostModule(ModuleBase):
            def get_name(self):
                return ModuleBase.MODULE_TYPE_SWITCH_HOST

        switch_host = SwitchHostModule()
        chassis = ChassisBase()
        chassis._module_list = [switch_host]

        assert chassis.get_num_modules() == 1
        assert chassis.get_all_modules() == [switch_host]
        assert chassis.get_module(0) is switch_host

    def test_pdbs(self, capsys):
        chassis = ChassisBase()
        assert chassis.get_num_pdbs() == 0
        assert chassis.get_all_pdbs() == []
        assert chassis.get_pdb(0) is None
        err = capsys.readouterr().err
        assert "PDB index 0 out of range" in err

        pdb0 = object()
        chassis._pdb_list = [pdb0]
        assert chassis.get_num_pdbs() == 1
        assert chassis.get_all_pdbs() == [pdb0]
        assert chassis.get_pdb(0) is pdb0

        assert chassis.get_pdb(1) is None
        err_oob = capsys.readouterr().err
        assert "PDB index 1 out of range (0-0)" in err_oob

    def test_pdbs_multiple_and_negative_index(self, capsys):
        """Several PDB entries: success paths, high index error, valid negative index."""
        chassis = ChassisBase()
        pdb0, pdb1, pdb2 = object(), object(), object()
        chassis._pdb_list = [pdb0, pdb1, pdb2]

        assert chassis.get_num_pdbs() == 3
        assert chassis.get_all_pdbs() == [pdb0, pdb1, pdb2]
        assert chassis.get_pdb(0) is pdb0
        assert chassis.get_pdb(1) is pdb1
        assert chassis.get_pdb(2) is pdb2
        capsys.readouterr()

        assert chassis.get_pdb(3) is None
        err_high = capsys.readouterr().err
        assert "PDB index 3 out of range (0-2)" in err_high

        assert chassis.get_pdb(-1) is pdb2
        assert chassis.get_pdb(-2) is pdb1
        assert chassis.get_pdb(-3) is pdb0

        assert chassis.get_pdb(-4) is None
        err_neg = capsys.readouterr().err
        assert "PDB index -4 out of range (0-2)" in err_neg

    def test_device_info_import_failure(self):
        # Some unit-test packages shadow sonic_py_common with a partial mock
        # that does not provide device_info. chassis_base must still import
        # successfully so these tests do not fail, since device_info is only
        # required by some platform features.
        real_import = builtins.__import__

        def failing_import(name, *args, **kwargs):
            if name == "sonic_py_common":
                raise ImportError("no module named sonic_py_common.device_info")
            return real_import(name, *args, **kwargs)

        try:
            with mock.patch.object(builtins, "__import__", failing_import):
                importlib.reload(chassis_base)

            assert chassis_base.device_info is None
            chassis_base.ChassisBase()
        finally:
            # Restore the module for the remaining tests
            importlib.reload(chassis_base)

        assert chassis_base.device_info is not None
