# Magic seed layout for static_comparator; generated from specs/comparator.yaml.
# This is a deterministic PCell route seed for tool-flow validation.
proc make_pin {name x y num} {
    units microns
    box position $x $y
    box size 1 1
    paint metal1
    label $name FreeSans 1 0 0 0 c metal1
    port make $num
}

load static_comparator -force
units microns
box position 0.000 0.000
magic::gencell sky130::sky130_fd_pr__nfet_01v8 XMN -spice w 1 l 0.15 nf 1 m 1 guard 1 doports 1
box position 0.000 10.000
magic::gencell sky130::sky130_fd_pr__pfet_01v8 XMP -spice w 2.5 l 0.15 nf 1 m 1 guard 1 doports 1
make_pin vin -6.000 6.000 0
make_pin out 8.000 6.000 1
make_pin vdd 8.000 16.000 2
make_pin vss 8.000 -4.000 3
proc draw_routes {} {

    # Comparator route seed: metal1 device stubs, metal2 vertical buses.
    box 0.440 -0.350 1.140 0.350
    paint locali
    box 0.440 -0.350 1.140 0.350
    paint metal1
    box 0.620 -0.170 0.960 0.170
    paint viali
    box 0.440 9.650 1.140 10.350
    paint locali
    box 0.440 9.650 1.140 10.350
    paint metal1
    box 0.620 9.830 0.960 10.170
    paint viali
    # net vin
    box -4.250 1.460 -3.750 14.250
    paint metal2
    box -5.500 6.400 -4.000 6.600
    paint metal1
    box -4.350 6.150 -3.650 6.850
    paint metal1
    box -4.350 6.150 -3.650 6.850
    paint metal2
    box -4.170 6.330 -3.830 6.670
    paint via1
    box -4.000 1.960 0.790 2.160
    paint metal1
    box -4.350 1.710 -3.650 2.410
    paint metal1
    box -4.350 1.710 -3.650 2.410
    paint metal2
    box -4.170 1.890 -3.830 2.230
    paint via1
    box -4.000 13.550 0.790 13.750
    paint metal1
    box -4.350 13.300 -3.650 14.000
    paint metal1
    box -4.350 13.300 -3.650 14.000
    paint metal2
    box -4.170 13.480 -3.830 13.820
    paint via1
    # net out
    box -1.250 0.685 -0.750 12.680
    paint metal2
    box -1.000 6.400 8.500 6.600
    paint metal1
    box -1.350 6.150 -0.650 6.850
    paint metal1
    box -1.350 6.150 -0.650 6.850
    paint metal2
    box -1.170 6.330 -0.830 6.670
    paint via1
    box -1.000 1.185 0.570 1.385
    paint metal1
    box -1.350 0.935 -0.650 1.635
    paint metal1
    box -1.350 0.935 -0.650 1.635
    paint metal2
    box -1.170 1.115 -0.830 1.455
    paint via1
    box -1.000 11.980 0.570 12.180
    paint metal1
    box -1.350 11.730 -0.650 12.430
    paint metal1
    box -1.350 11.730 -0.650 12.430
    paint metal2
    box -1.170 11.910 -0.830 12.250
    paint via1
    # net vdd
    box 8.750 9.400 9.250 17.100
    paint metal2
    box 8.500 16.400 9.000 16.600
    paint metal1
    box 8.650 16.150 9.350 16.850
    paint metal1
    box 8.650 16.150 9.350 16.850
    paint metal2
    box 8.830 16.330 9.170 16.670
    paint via1
    box 0.790 9.900 9.000 10.100
    paint metal1
    box 8.650 9.650 9.350 10.350
    paint metal1
    box 8.650 9.650 9.350 10.350
    paint metal2
    box 8.830 9.830 9.170 10.170
    paint via1
    box 1.010 11.980 9.000 12.180
    paint metal1
    box 8.650 11.730 9.350 12.430
    paint metal1
    box 8.650 11.730 9.350 12.430
    paint metal2
    box 8.830 11.910 9.170 12.250
    paint via1
    # net vss
    box 9.750 -4.100 10.250 1.885
    paint metal2
    box 8.500 -3.600 10.000 -3.400
    paint metal1
    box 9.650 -3.850 10.350 -3.150
    paint metal1
    box 9.650 -3.850 10.350 -3.150
    paint metal2
    box 9.830 -3.670 10.170 -3.330
    paint via1
    box 0.790 -0.100 10.000 0.100
    paint metal1
    box 9.650 -0.350 10.350 0.350
    paint metal1
    box 9.650 -0.350 10.350 0.350
    paint metal2
    box 9.830 -0.170 10.170 0.170
    paint via1
    box 1.010 1.185 10.000 1.385
    paint metal1
    box 9.650 0.935 10.350 1.635
    paint metal1
    box 9.650 0.935 10.350 1.635
    paint metal2
    box 9.830 1.115 10.170 1.455
    paint via1
    # boundary fill-free marker
    box -7.000 -5.000 -6.800 17.500
    paint metal1
}
draw_routes
save static_comparator
writeall force
quit -noprompt
