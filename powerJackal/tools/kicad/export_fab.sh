#!/bin/bash
# Fab outputs from the finished board. usage: export_fab.sh <board.kicad_pcb> <outdir>
set -e
PCB=$1; OUT=$2
rm -rf $OUT/fab && mkdir -p $OUT/fab/gerbers
kicad-cli pcb export gerbers -l F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask --use-drill-file-origin -o $OUT/fab/gerbers/ $PCB >/dev/null
kicad-cli pcb export drill --excellon-separate-th --excellon-oval-format route --drill-origin plot -o $OUT/fab/gerbers/ $PCB >/dev/null
kicad-cli pcb export pos --format csv --units mm --side front --use-drill-file-origin -o $OUT/fab/powerJackal_positions_top.csv $PCB >/dev/null
(cd $OUT/fab && zip -q -j jackal_gerbers.zip gerbers/*)
echo "fab outputs in $OUT/fab"
