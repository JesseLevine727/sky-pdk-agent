# Relocate a locally extracted Netgen Tcl startup into this repository.

if {![info exists env(NETGEN_LOCAL_ROOT)]} {
    puts stderr "NETGEN_LOCAL_ROOT is not set"
    exit 1
}

set netgen_root $env(NETGEN_LOCAL_ROOT)
set CAD_ROOT [file dirname $netgen_root]
set env(CAD_ROOT) $CAD_ROOT
set startup [file join $netgen_root tcl netgen.tcl]

if {![file exists $startup]} {
    puts stderr "missing Netgen startup script: $startup"
    exit 1
}

set handle [open $startup r]
set startup_script [read $handle]
close $handle

set startup_script [string map [list "/usr/lib/netgen" $netgen_root] $startup_script]

if {[catch {uplevel #0 $startup_script} result options]} {
    puts stderr $result
    exit 1
}
