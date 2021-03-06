package FS::ClientAPI;

use strict;
use base 'Exporter';
use vars qw( @EXPORT_OK %handler $domain $DEBUG $me );

@EXPORT_OK = qw( load_clientapi_modules );

$DEBUG = 0;
$me = '[FS::ClientAPI]';

%handler = ();

=head1 NAME

FS::ClientAPI

=item load_clientapi_modules

=cut

sub load_clientapi_modules {

  #find modules
  foreach my $INC ( @INC ) {
    my $glob = "$INC/FS/ClientAPI/*.pm";
    warn "FS::ClientAPI: searching $glob" if $DEBUG;
    foreach my $file ( glob($glob) ) {
      $file =~ /\/(\w+)\.pm$/ or do {
        warn "unrecognized ClientAPI file: $file";
        next
      };
      my $mod = $1;
      warn "using FS::ClientAPI::$mod" if $DEBUG;
      eval "use FS::ClientAPI::$mod;";
      die "error using FS::ClientAPI::$mod: $@" if $@;
    }
  }

}

=item dispatch [ name ]

=cut

sub dispatch {
  my ( $self, $name ) = ( shift, shift );
  $name =~ s(/)(::)g;
  my $sub = "FS::ClientAPI::$name";
  warn "$me dispatch: calling $sub with args @_\n" if $DEBUG;
  no strict 'refs';
  &{$sub}(@_);
}

1;

