# Magic seed layout for ota_5t; generated from specs/ota.yaml.
# This is a deterministic PCell route seed for tool-flow validation.
proc make_pin {name x y num} {
    units microns
    box position $x $y
    box size 1 1
    paint metal1
    label $name FreeSans 1 0 0 0 c metal1
    port make $num
}

load ota_5t -force
units microns
box position 0.000 30.000
magic::gencell sky130::sky130_fd_pr__pfet_01v8 XMP_DIODE -spice w 26 l 1.05 nf 1 m 1 guard 1 doports 1
box position 12.000 30.000
magic::gencell sky130::sky130_fd_pr__pfet_01v8 XMP_MIRROR -spice w 26 l 1.05 nf 1 m 1 guard 1 doports 1
box position 0.000 5.000
magic::gencell sky130::sky130_fd_pr__nfet_01v8 XMN_INP -spice w 15.12 l 1.05 nf 1 m 1 guard 1 doports 1
box position 12.000 5.000
magic::gencell sky130::sky130_fd_pr__nfet_01v8 XMN_INN -spice w 15.12 l 1.05 nf 1 m 1 guard 1 doports 1
box position 6.000 -20.000
magic::gencell sky130::sky130_fd_pr__nfet_01v8 XMN_TAIL -spice w 8 l 1 nf 1 m 1 guard 1 doports 1
make_pin inp -15.000 24.000 0
make_pin inn 17.500 24.000 1
make_pin out 9.500 45.000 2
make_pin vdd 21.500 45.000 3
make_pin vss 23.500 -25.000 4
make_pin bias -5.000 -25.000 5
proc draw_routes {} {

    # Two-layer deterministic route seed: metal1 terminal stubs, metal2 buses.
    # Body terminals use local-interconnect-to-metal1 contact stacks.
    box 0.890 29.650 1.590 30.350
    paint locali
    box 0.890 29.650 1.590 30.350
    paint metal1
    box 1.070 29.830 1.410 30.170
    paint viali
    box 12.890 29.650 13.590 30.350
    paint locali
    box 12.890 29.650 13.590 30.350
    paint metal1
    box 13.070 29.830 13.410 30.170
    paint viali
    box 0.890 4.650 1.590 5.350
    paint locali
    box 0.890 4.650 1.590 5.350
    paint metal1
    box 1.070 4.830 1.410 5.170
    paint viali
    box 12.890 4.650 13.590 5.350
    paint locali
    box 12.890 4.650 13.590 5.350
    paint metal1
    box 13.070 4.830 13.410 5.170
    paint viali
    box 6.865 -20.350 7.565 -19.650
    paint locali
    box 6.865 -20.350 7.565 -19.650
    paint metal1
    box 7.045 -20.170 7.385 -19.830
    paint viali
    # net inp
    box -14.250 20.580 -13.750 25.100
    paint metal2
    box -14.500 24.400 -14.000 24.600
    paint metal1
    box -14.350 24.150 -13.650 24.850
    paint metal1
    box -14.350 24.150 -13.650 24.850
    paint metal2
    box -14.170 24.330 -13.830 24.670
    paint via1
    box -14.000 21.080 1.240 21.280
    paint metal1
    box -14.350 20.830 -13.650 21.530
    paint metal1
    box -14.350 20.830 -13.650 21.530
    paint metal2
    box -14.170 21.010 -13.830 21.350
    paint via1
    # net out
    box 9.750 11.345 10.250 46.100
    paint metal2
    box 10.000 45.400 10.000 45.600
    paint metal1
    box 9.650 45.150 10.350 45.850
    paint metal1
    box 9.650 45.150 10.350 45.850
    paint metal2
    box 9.830 45.330 10.170 45.670
    paint via1
    box 12.470 11.945 12.670 13.345
    paint metal1
    box 10.000 11.845 12.570 12.045
    paint metal1
    box 9.650 11.595 10.350 12.295
    paint metal1
    box 9.650 11.595 10.350 12.295
    paint metal2
    box 9.830 11.775 10.170 12.115
    paint via1
    box 12.470 42.430 12.670 43.830
    paint metal1
    box 10.000 42.330 12.570 42.530
    paint metal1
    box 9.650 42.080 10.350 42.780
    paint metal1
    box 9.650 42.080 10.350 42.780
    paint metal2
    box 9.830 42.260 10.170 42.600
    paint via1
    # net vdd
    box 21.750 29.400 22.250 59.750
    paint metal2
    box 22.000 45.400 22.000 45.600
    paint metal1
    box 21.650 45.150 22.350 45.850
    paint metal1
    box 21.650 45.150 22.350 45.850
    paint metal2
    box 21.830 45.330 22.170 45.670
    paint via1
    box 1.240 29.900 22.000 30.100
    paint metal1
    box 21.650 29.650 22.350 30.350
    paint metal1
    box 21.650 29.650 22.350 30.350
    paint metal2
    box 21.830 29.830 22.170 30.170
    paint via1
    box 13.240 29.900 22.000 30.100
    paint metal1
    box 21.650 29.650 22.350 30.350
    paint metal1
    box 21.650 29.650 22.350 30.350
    paint metal2
    box 21.830 29.830 22.170 30.170
    paint via1
    box 1.810 43.830 2.010 59.150
    paint metal1
    box 1.910 59.050 22.000 59.250
    paint metal1
    box 21.650 58.800 22.350 59.500
    paint metal1
    box 21.650 58.800 22.350 59.500
    paint metal2
    box 21.830 58.980 22.170 59.320
    paint via1
    box 13.810 43.830 14.010 59.150
    paint metal1
    box 13.910 59.050 22.000 59.250
    paint metal1
    box 21.650 58.800 22.350 59.500
    paint metal1
    box 21.650 58.800 22.350 59.500
    paint metal2
    box 21.830 58.980 22.170 59.320
    paint via1
    # net vss
    box 23.750 -25.100 24.250 5.600
    paint metal2
    box 24.000 -24.600 24.000 -24.400
    paint metal1
    box 23.650 -24.850 24.350 -24.150
    paint metal1
    box 23.650 -24.850 24.350 -24.150
    paint metal2
    box 23.830 -24.670 24.170 -24.330
    paint via1
    box 1.240 4.900 24.000 5.100
    paint metal1
    box 23.650 4.650 24.350 5.350
    paint metal1
    box 23.650 4.650 24.350 5.350
    paint metal2
    box 23.830 4.830 24.170 5.170
    paint via1
    box 13.240 4.900 24.000 5.100
    paint metal1
    box 23.650 4.650 24.350 5.350
    paint metal1
    box 23.650 4.650 24.350 5.350
    paint metal2
    box 23.830 4.830 24.170 5.170
    paint via1
    box 7.215 -20.100 24.000 -19.900
    paint metal1
    box 23.650 -20.350 24.350 -19.650
    paint metal1
    box 23.650 -20.350 24.350 -19.650
    paint metal2
    box 23.830 -20.170 24.170 -19.830
    paint via1
    box 7.760 -16.415 7.960 -15.215
    paint metal1
    box 7.860 -16.515 24.000 -16.315
    paint metal1
    box 23.650 -16.765 24.350 -16.065
    paint metal1
    box 23.650 -16.765 24.350 -16.065
    paint metal2
    box 23.830 -16.585 24.170 -16.245
    paint via1
    # net bias
    box -4.250 -25.100 -3.750 -10.340
    paint metal2
    box -4.500 -24.600 -4.000 -24.400
    paint metal1
    box -4.350 -24.850 -3.650 -24.150
    paint metal1
    box -4.350 -24.850 -3.650 -24.150
    paint metal2
    box -4.170 -24.670 -3.830 -24.330
    paint via1
    box -4.000 -11.040 7.215 -10.840
    paint metal1
    box -4.350 -11.290 -3.650 -10.590
    paint metal1
    box -4.350 -11.290 -3.650 -10.590
    paint metal2
    box -4.170 -11.110 -3.830 -10.770
    paint via1
    # net inn
    box 17.750 20.580 18.250 25.100
    paint metal2
    box 18.000 24.400 18.000 24.600
    paint metal1
    box 17.650 24.150 18.350 24.850
    paint metal1
    box 17.650 24.150 18.350 24.850
    paint metal2
    box 17.830 24.330 18.170 24.670
    paint via1
    box 12.890 20.830 13.590 21.530
    paint metal1
    box 12.890 20.830 13.590 21.530
    paint metal2
    box 13.070 21.010 13.410 21.350
    paint via1
    box 12.890 20.830 13.590 21.530
    paint metal2
    box 12.890 20.830 13.590 21.530
    paint metal3
    box 13.060 21.000 13.420 21.360
    paint via2
    box 13.240 20.930 18.000 21.430
    paint metal3
    box 17.650 20.830 18.350 21.530
    paint metal2
    box 17.650 20.830 18.350 21.530
    paint metal3
    box 17.820 21.000 18.180 21.360
    paint via2
    # net outn
    box -2.250 12.745 -1.750 57.750
    paint metal2
    box -2.000 13.245 0.570 13.445
    paint metal1
    box -2.350 12.995 -1.650 13.695
    paint metal1
    box -2.350 12.995 -1.650 13.695
    paint metal2
    box -2.170 13.175 -1.830 13.515
    paint via1
    box -2.000 43.730 0.570 43.930
    paint metal1
    box -2.350 43.480 -1.650 44.180
    paint metal1
    box -2.350 43.480 -1.650 44.180
    paint metal2
    box -2.170 43.660 -1.830 44.000
    paint via1
    box 0.890 56.800 1.590 57.500
    paint metal1
    box 0.890 56.800 1.590 57.500
    paint metal2
    box 1.070 56.980 1.410 57.320
    paint via1
    box 0.890 56.800 1.590 57.500
    paint metal2
    box 0.890 56.800 1.590 57.500
    paint metal3
    box 1.060 56.970 1.420 57.330
    paint via2
    box -2.000 56.900 1.240 57.400
    paint metal3
    box -2.350 56.800 -1.650 57.500
    paint metal2
    box -2.350 56.800 -1.650 57.500
    paint metal3
    box -2.180 56.970 -1.820 57.330
    paint via2
    box 12.890 56.800 13.590 57.500
    paint metal1
    box 12.890 56.800 13.590 57.500
    paint metal2
    box 13.070 56.980 13.410 57.320
    paint via1
    box 12.890 56.800 13.590 57.500
    paint metal2
    box 12.890 56.800 13.590 57.500
    paint metal3
    box 13.060 56.970 13.420 57.330
    paint via2
    box -2.000 56.900 13.240 57.400
    paint metal3
    box -2.350 56.800 -1.650 57.500
    paint metal2
    box -2.350 56.800 -1.650 57.500
    paint metal3
    box -2.180 56.970 -1.820 57.330
    paint via2
    # net tail
    box 3.750 -14.515 4.250 0.600
    paint metal2
    box 19.750 -0.600 20.250 23.780
    paint metal2
    box 6.470 -15.215 6.670 -13.915
    paint metal1
    box 4.000 -14.015 6.570 -13.815
    paint metal1
    box 3.650 -14.265 4.350 -13.565
    paint metal1
    box 3.650 -14.265 4.350 -13.565
    paint metal2
    box 3.830 -14.085 4.170 -13.745
    paint via1
    box 1.810 13.345 2.010 23.180
    paint metal1
    box 1.910 23.080 20.000 23.280
    paint metal1
    box 19.650 22.830 20.350 23.530
    paint metal1
    box 19.650 22.830 20.350 23.530
    paint metal2
    box 19.830 23.010 20.170 23.350
    paint via1
    box 13.810 13.345 14.010 23.180
    paint metal1
    box 13.910 23.080 20.000 23.280
    paint metal1
    box 19.650 22.830 20.350 23.530
    paint metal1
    box 19.650 22.830 20.350 23.530
    paint metal2
    box 19.830 23.010 20.170 23.350
    paint via1
    box 4.000 -0.100 20.000 0.100
    paint metal1
    box 3.650 -0.350 4.350 0.350
    paint metal1
    box 3.650 -0.350 4.350 0.350
    paint metal2
    box 3.830 -0.170 4.170 0.170
    paint via1
    box 19.650 -0.350 20.350 0.350
    paint metal1
    box 19.650 -0.350 20.350 0.350
    paint metal2
    box 19.830 -0.170 20.170 0.170
    paint via1
}
draw_routes
save ota_5t
writeall force
quit -noprompt
