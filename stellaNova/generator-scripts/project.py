"""Write the .kicad_pro: design rules and net classes (KiCad 7 format)."""
import json, sys, os

def write(path, root_uuid):
    nc_default = dict(name='Default', clearance=0.15, track_width=0.2, via_diameter=0.6, via_drill=0.3,
                      microvia_diameter=0.3, microvia_drill=0.1, diff_pair_width=0.2, diff_pair_gap=0.15,
                      diff_pair_via_gap=0.25, wire_width=6, bus_width=12, line_style=0, pcb_color='rgba(0, 0, 0, 0.000)',
                      schematic_color='rgba(0, 0, 0, 0.000)')
    power = dict(nc_default, name='Power', clearance=0.2, track_width=0.4, via_diameter=0.6, via_drill=0.3)
    rail = dict(nc_default, name='Rail', clearance=0.15, track_width=0.3, via_diameter=0.6, via_drill=0.3)
    usb = dict(nc_default, name='USB', clearance=0.15, track_width=0.25, diff_pair_width=0.25, diff_pair_gap=0.15)
    pro = {
        'board': {
            'design_settings': {
                'defaults': {
                    'board_outline_line_width': 0.1, 'copper_line_width': 0.2, 'copper_text_size_h': 1.0,
                    'copper_text_size_v': 1.0, 'copper_text_thickness': 0.15, 'silk_line_width': 0.12,
                    'silk_text_size_h': 0.8, 'silk_text_size_v': 0.8, 'silk_text_thickness': 0.12,
                    'fab_line_width': 0.1, 'fab_text_size_h': 1.0, 'fab_text_size_v': 1.0, 'fab_text_thickness': 0.15,
                    'courtyard_line_width': 0.05, 'other_line_width': 0.1,
                    'pads': {'drill': 0.8, 'height': 1.4, 'width': 1.4},
                    'zones': {'min_clearance': 0.25},
                },
                'diff_pair_dimensions': [{'gap': 0.0, 'via_gap': 0.0, 'width': 0.0}, {'gap': 0.15, 'via_gap': 0.25, 'width': 0.25}],
                'meta': {'version': 2},
                'rule_severities': {
                    'silk_overlap': 'ignore', 'silk_over_copper': 'warning', 'silk_edge_clearance': 'ignore',
                    'lib_footprint_issues': 'ignore', 'lib_footprint_mismatch': 'ignore',
                    'text_height': 'ignore', 'text_thickness': 'ignore',
                },
                'rules': {
                    'allow_blind_buried_vias': False, 'allow_microvias': False,
                    'max_error': 0.005, 'min_clearance': 0.15, 'min_connection': 0.12,
                    'min_copper_edge_clearance': 0.3, 'min_hole_clearance': 0.19, 'min_hole_to_hole': 0.25,
                    'min_microvia_diameter': 0.2, 'min_microvia_drill': 0.1, 'min_resolved_spokes': 1,
                    'min_silk_clearance': 0.0, 'min_text_height': 0.6, 'min_text_thickness': 0.08,
                    'min_through_hole_diameter': 0.2, 'min_track_width': 0.15, 'min_via_annular_width': 0.1,
                    'min_via_diameter': 0.45, 'solder_mask_to_copper_clearance': 0.0, 'use_height_for_length_calcs': True,
                },
                'track_widths': [0.0, 0.2, 0.25, 0.3, 0.5, 0.8],
                'via_dimensions': [{'diameter': 0.0, 'drill': 0.0}, {'diameter': 0.6, 'drill': 0.3}, {'diameter': 0.8, 'drill': 0.4}],
                'zones_allow_external_fillets': False, 'zones_use_no_outline': True,
            },
            'layer_presets': [], 'viewports': [],
        },
        'boards': [], 'cvpcb': {'equivalence_files': []},
        'libraries': {'pinned_footprint_libs': [], 'pinned_symbol_libs': []},
        'meta': {'filename': os.path.basename(path), 'version': 1},
        'net_settings': {
            'classes': [nc_default, power, rail, usb],
            'meta': {'version': 3},
            'net_colors': None,
            'netclass_assignments': None,
            'netclass_patterns': [{'netclass': 'Power', 'pattern': p} for p in
                                  ('VIN', '/VBAT_PORT', 'Net-(D2-A)', '/SW')] +
                                 [{'netclass': 'Rail', 'pattern': p} for p in ('+3V3', 'GND', 'VBUS')] +
                                 [{'netclass': 'USB', 'pattern': p} for p in ('/USB_DP', '/USB_DN', '/ESP_USB_DP', '/ESP_USB_DN')],
        },
        'pcbnew': {'last_paths': {}, 'page_layout_descr_file': ''},
        'schematic': {'legacy_lib_dir': '', 'legacy_lib_list': []},
        'sheets': [[root_uuid, '']],
        'text_variables': {},
    }
    json.dump(pro, open(path, 'w'), indent=2)
