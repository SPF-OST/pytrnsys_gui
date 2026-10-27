import os
import sys
import pathlib as _pl
import matplotlib.pyplot as _plt
from pytrnsys_process import api


def solar(sim: api.Simulation):
    #### Plots ####
    fig, ax = api.line_plot(sim.hourly, ["Pcoll_kW"])
    ax.set_ylabel("Power (kW)")
    _plt.grid()
    # _plt.show()
    api.export_plots_in_configured_formats(fig, sim.path, "P-hourly", "solar")

    fig, ax = api.bar_chart(sim.monthly, ["Pcoll_kW"])
    ax.set_ylabel("Power (kW)")
    _plt.grid()
    # _plt.show()
    api.export_plots_in_configured_formats(fig, sim.path, "P-monthlÿ", "solar")


    fig, ax = api.line_plot(sim.hourly, ["TCollOut", "TCollIn"])
    ax.set_ylabel("Temperature (°C)")
    _plt.grid()
    # _plt.show()
    api.export_plots_in_configured_formats(fig, sim.path, "T-hourly", "solar")


def tank(sim: api.Simulation):
    #### Plots ####
    fig, ax = api.line_plot(sim.hourly, ["T1_Tes1","T2_Tes1","T3_Tes1","T4_Tes1","T5_Tes1","T6_Tes1","T7_Tes1","T8_Tes1","T9_Tes1","T10_Tes1"])
    ax.set_ylabel("Temperature (°C)")
    _plt.grid()
    # _plt.show()
    api.export_plots_in_configured_formats(fig, sim.path, "T-hourly", "tank")

def demand(sim: api.Simulation):
    ### Plots ###
    fig, ax = api.line_plot(sim.hourly, ["Pdhw_kW"])
    ax.set_ylabel("Power (kW)")
    _plt.grid()
    # _plt.show()
    api.export_plots_in_configured_formats(fig, sim.path, "P-hourly", "demand")

    fig, ax = api.bar_chart(sim.monthly, ["Pdhw_kW"])
    ax.set_ylabel("Power (kW)")
    _plt.grid()
    # _plt.show()
    api.export_plots_in_configured_formats(fig, sim.path, "P-monthly", "demand")



if __name__ == "__main__":

    path_to_sim = _pl.Path("./results")
    api.global_settings.reader.force_reread_prt = False
    api.global_settings.reader.read_step_files = True

    processing_steps = [
        solar,
        tank,
        demand
        ]

    simulation_data = api.process_whole_result_set(
        path_to_sim,
        processing_steps,
    )


