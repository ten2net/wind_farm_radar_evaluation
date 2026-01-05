DEFAULT_RADAR_PARAMS = {
    'transmitter': {
        'frequency_hz': 1e9,
        'power_w': 100000,
        'pulse_width_s': 100e-6,
        'prf_hz': 1000
    },
    'antenna': {
        'gain_dbi': 30.0,
        'azimuth_beamwidth': 5.0,
        'elevation_beamwidth': 10.0
    },
    'signal_processing': {
        'mti_filter': '3脉冲对消器',
        'doppler_channels': 256,
        'max_tracking_targets': 100
    }
}