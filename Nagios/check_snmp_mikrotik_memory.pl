#!/usr/bin/perl -w 

###################################
#
# written by Ahsan Md Sajid Khan
#      
# This script will return Main Memory and System Disk Usage status only.  
# Critical and Warning Threshold will work only for Main Memory.
#
###################################

use strict;
use Net::SNMP;
use Getopt::Long;

use lib "/usr/lib/nagios/plugins/";
use utils qw($TIMEOUT %ERRORS);



my $STORAGE_NAME = '1.3.6.1.2.1.25.2.3.1.3';
my $STORAGE_SIZE = '1.3.6.1.2.1.25.2.3.1.5';
my $STORAGE_USAGE = '1.3.6.1.2.1.25.2.3.1.6';
my $ALLOCATION_FAILURE = '1.3.6.1.2.1.25.2.3.1.7';

my $returnstring = "";
my $perf_data = "";
my $returnvalue = $ERRORS{"OK"};


my $host = 	undef;
my $community = undef;
my $warning = undef;
my $critical = undef;
my $help = undef;

Getopt::Long::Configure ("bundling");
GetOptions(
	'h' => \$help,
	'help' => \$help,
	'c:s' => \$critical,
	'critical:s' => \$critical,
	'w:s' => \$warning,
	'warn:s' => \$warning,
	'H:s' => \$host,
	'host:s' => \$host,
	'C:s' => \$community,
	'community:s' => \$community
);

sub nonum
{
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}
sub print_usage
{
    print "Usage: $0 -H <host> -C <COMMUNITY-STRING> -w <WARNLEVEL in %>  -c <CRITLEVEL in %>\n";
}

# CHECKS
if ( defined($help) )
{
	print_usage();
	exit $ERRORS{"UNKNOWN"};
}
if ( !defined($host) )
{
	print "Need Host-Address!\n";
	print_usage();
	exit $ERRORS{"UNKNOWN"};
}
if ( !defined($community) )
{
	print "Need Community-String!\n";
	print_usage();
	exit $ERRORS{"UNKNOWN"};
}
if (!defined($warning) || !defined($critical))
{
	print "Need Warning- and Critical-Info!\n";
	print_usage();
	exit $ERRORS{"UNKNOWN"};
}
$warning =~ s/\%//g; 
$critical =~ s/\%//g;
if ( nonum($warning) || nonum($critical))
{
	print "Only numerical Values for crit/warn allowed !\n";
	print_usage();
	exit $ERRORS{"UNKNOWN"}
}
if ($warning > $critical) 
{
	print "warning <= critical ! \n";
	print_usage();
	exit $ERRORS{"UNKNOWN"}
}

my ($session, $error) = Net::SNMP->session( -hostname  => $host, -version   => 2, -community => $community, -timeout   => $TIMEOUT);

if (!defined($session)) {
   printf("ERROR opening session: %s.\n", $error);
   exit $ERRORS{"CRITICAL"};
}

my $storage_name = $session->get_table(-baseoid => $STORAGE_NAME);
if (!defined($storage_name))
{
   printf("ERROR: Description table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"CRITICAL"};
}




my $storage_size = $session->get_table(-baseoid => $STORAGE_SIZE);
if (!defined($storage_size))
{
   printf("ERROR: Description table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"CRITICAL"};
}

my $storage_usage = $session->get_table(-baseoid => $STORAGE_USAGE);
if (!defined($storage_usage))
{
   printf("ERROR: Description table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"CRITICAL"};
}

my $storage_failure = $session->get_table(-baseoid => $ALLOCATION_FAILURE);
if (!defined($storage_failure))
{
   printf("ERROR: Description table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"CRITICAL"};
}





my @storage_pools = keys %$storage_name;

for(my $pool = 1; $pool <= @storage_pools; $pool++)
{




        my @name = split (/:/,  $$storage_name{$storage_pools[$pool-1]});

        #     $returnstring .=" "."Memory Name : ".$name[0]; # delete it

        my $id = ((split(/\./, $storage_pools[$pool - 1])) [-1]);
        my $size = $$storage_size{$STORAGE_SIZE.".".$id};
        my $usage = $$storage_usage{$STORAGE_USAGE.".".$id};
        my $failure = $$storage_failure{$ALLOCATION_FAILURE.".".$id};
        my $size_mb = $size/1000;
           $size_mb = sprintf "%.2f",$size_mb;
        my $usage_mb = $usage/1000;
           $usage_mb = sprintf "%.2f",$usage_mb;
        my $usage_percent = $size/$usage;
           $usage_percent = sprintf "%.2f",$usage_percent;

       # printf ("ID = ". $id."Usage Percentage=".$usage_percent." Size = ".$size_mb." MBytes Usage = ".$usage_mb."MBytes Failure = ".$failure."\n"); # delete it

       $returnstring .=" ".$name[0]." : Usage=".$usage_percent."% Total Size=".$size_mb."MBytes Total Used=".$usage_mb."MBytes Storage Allocation Failure=".$failure;

       if($name[0] eq "main memory")        
       {
         my $size_bit = $size*8;
         my $usage_bit = $usage*8;
         $perf_data="memory_size=".$size_bit." memory_used=".$usage_bit;
       }

       if($usage_percent >=$warning)
        { $returnvalue = $ERRORS{"WARNING"}}

        if($usage_percent >=$critical)
         { $returnvalue = $ERRORS{"CRITICAL"}}

        



}

$returnstring=$returnstring."|".$perf_data;



if ($returnvalue == $ERRORS{"CRITICAL"})
{
	print "CRITICAL: ".$returnstring."\n";
	exit $returnvalue;
}


if ($returnvalue == $ERRORS{"WARNING"})
{
	print "WARNING: ".$returnstring."\n";
	exit $returnvalue;
}

print "OK: ".$returnstring."\n";
exit $returnvalue;
