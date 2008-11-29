package FS::svc_phone;

use strict;
use vars qw( @ISA @pw_set );
use FS::Conf;
#use FS::Record qw( qsearch qsearchs );
use FS::svc_Common;

@ISA = qw( FS::svc_Common );

#avoid l 1 and o O 0
@pw_set = ( 'a'..'k', 'm','n', 'p-z', 'A'..'N', 'P'..'Z' , '2'..'9' );

=head1 NAME

FS::svc_phone - Object methods for svc_phone records

=head1 SYNOPSIS

  use FS::svc_phone;

  $record = new FS::svc_phone \%hash;
  $record = new FS::svc_phone { 'column' => 'value' };

  $error = $record->insert;

  $error = $new_record->replace($old_record);

  $error = $record->delete;

  $error = $record->check;

  $error = $record->suspend;

  $error = $record->unsuspend;

  $error = $record->cancel;

=head1 DESCRIPTION

An FS::svc_phone object represents a phone number.  FS::svc_phone inherits
from FS::Record.  The following fields are currently supported:

=over 4

=item svcnum

primary key

=item countrycode

=item phonenum

=item sip_password

=item pin

Voicemail PIN

=item phone_name

=back

=head1 METHODS

=over 4

=item new HASHREF

Creates a new phone number.  To add the number to the database, see L<"insert">.

Note that this stores the hash reference, not a distinct copy of the hash it
points to.  You can ask the object for a copy with the I<hash> method.

=cut

# the new method can be inherited from FS::Record, if a table method is defined
#
sub table_info {
  {
    'name' => 'Phone number',
    'sorts' => 'phonenum',
    'display_weight' => 60,
    'cancel_weight'  => 80,
    'fields' => {
        'countrycode'  => { label => 'Country code',
                            type  => 'text',
                            disable_inventory => 1,
                            disable_select => 1,
                          },
        'phonenum'     => 'Phone number',
        'pin'          => { label => 'Personal Identification Number',
                            type  => 'text',
                            disable_inventory => 1,
                            disable_select => 1,
                          },
        'sip_password' => 'SIP password',
        'name'         => 'Name',
    },
  };
}

sub table { 'svc_phone'; }

=item search_sql STRING

Class method which returns an SQL fragment to search for the given string.

=cut

sub search_sql {
  my( $class, $string ) = @_;
  $class->search_sql_field('phonenum', $string );
}

=item label

Returns the phone number.

=cut

sub label {
  my $self = shift;
  my $phonenum = $self->phonenum; #XXX format it better
  my $label = $phonenum;
  $label .= ' ('.$self->phone_name.')' if $self->phone_name;
  $label;
}

=item insert

Adds this record to the database.  If there is an error, returns the error,
otherwise returns false.

=cut

# the insert method can be inherited from FS::Record

=item delete

Delete this record from the database.

=cut

# the delete method can be inherited from FS::Record

=item replace OLD_RECORD

Replaces the OLD_RECORD with this one in the database.  If there is an error,
returns the error, otherwise returns false.

=cut

# the replace method can be inherited from FS::Record

=item suspend

Called by the suspend method of FS::cust_pkg (see L<FS::cust_pkg>).

=item unsuspend

Called by the unsuspend method of FS::cust_pkg (see L<FS::cust_pkg>).

=item cancel

Called by the cancel method of FS::cust_pkg (see L<FS::cust_pkg>).

=item check

Checks all fields to make sure this is a valid phone number.  If there is
an error, returns the error, otherwise returns false.  Called by the insert
and replace methods.

=cut

# the check method should currently be supplied - FS::Record contains some
# data checking routines

sub check {
  my $self = shift;

  my $conf = new FS::Conf;

  my $phonenum = $self->phonenum;
  my $phonenum_check_method;
  if ( $conf->exists('svc_phone-allow_alpha_phonenum') ) {
    $phonenum =~ s/\W//g;
    $phonenum_check_method = 'ut_alpha';
  } else {
    $phonenum =~ s/\D//g;
    $phonenum_check_method = 'ut_number';
  }
  $self->phonenum($phonenum);

  my $error = 
    $self->ut_numbern('svcnum')
    || $self->ut_numbern('countrycode')
    || $self->$phonenum_check_method('phonenum')
    || $self->ut_anything('sip_password')
    || $self->ut_numbern('pin')
    || $self->ut_textn('phone_name')
  ;
  return $error if $error;

  $self->countrycode(1) unless $self->countrycode;

  unless ( length($self->sip_password) ) {

    $self->sip_password(
      join('', map $pw_set[ int(rand $#pw_set) ], (0..16) )
    );

  }

  $self->SUPER::check;
}

=item check_pin

Checks the supplied PIN against the PIN in the database.  Returns true for a
sucessful authentication, false if no match.

=cut

sub check_pin {
  my($self, $check_pin) = @_;
  length($self->pin) && $check_pin eq $self->pin;
}

=item radius_reply

=cut

sub radius_reply {
  my $self = shift;
  #XXX Session-Timeout!  holy shit, need rlm_perl to ask for this in realtime
  ();
}

=item radius_check

=cut

sub radius_check {
  my $self = shift;
  my %check = ();

  my $conf = new FS::Conf;

  $check{'User-Password'} = $conf->config('svc_phone-radius-default_password');

  %check;
}

sub radius_groups {
  ();
}

=back

=head1 BUGS

=head1 SEE ALSO

L<FS::svc_Common>, L<FS::Record>, L<FS::cust_svc>, L<FS::part_svc>,
L<FS::cust_pkg>, schema.html from the base documentation.

=cut

1;

