# Relocate a locally extracted Magic Tcl startup into this repository.
#
# Ubuntu Magic packages embed /usr/lib/x86_64-linux-gnu/magic/tcl paths in
# magic.tcl and magicdnull. The repo-local tool install extracts those files
# under .tools/apt, so the normal startup can silently degrade into a plain Tcl
# shell. This launcher patches the startup script in memory, then evaluates
# batch commands from stdin.

if {![info exists env(MAGIC_LOCAL_CAD_ROOT)]} {
    puts stderr "MAGIC_LOCAL_CAD_ROOT is not set"
    exit 1
}

set CAD_ROOT $env(MAGIC_LOCAL_CAD_ROOT)
set env(CAD_ROOT) $CAD_ROOT
set startup [file join $CAD_ROOT magic tcl magic.tcl]
set batch_script ""

if {[lsearch -exact $argv "--version"] < 0 && [lsearch -exact $argv "--prefix"] < 0} {
    if {![catch {chan configure stdin -blocking 0}]} {
        set batch_script [read stdin]
    }
}

if {![file exists $startup]} {
    puts stderr "missing Magic startup script: $startup"
    exit 1
}

set handle [open $startup r]
set startup_script [read $handle]
close $handle

set startup_script [string map [list "/usr/lib/x86_64-linux-gnu" $CAD_ROOT] $startup_script]

if {[catch {uplevel #0 $startup_script} result options]} {
    puts stderr $result
    exit 1
}

if {[string length [string trim $batch_script]] > 0} {
    if {[catch {uplevel #0 $batch_script} result options]} {
        puts stderr $result
        exit 1
    }
}
