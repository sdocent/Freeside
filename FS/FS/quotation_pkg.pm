package FS::quotation_pkg;
use base qw( FS::TemplateItem_Mixin FS::Record );

use strict;
use FS::Record qw( qsearchs qsearch dbh );
use FS::part_pkg;
use FS::quotation_pkg_discount; #so its loaded when TemplateItem_Mixin needs it
use FS::quotation_pkg_detail;
use List::Util qw(sum);

=head1 NAME

FS::quotation_pkg - Object methods for quotation_pkg records

=head1 SYNOPSIS

  use FS::quotation_pkg;

  $record = new FS::quotation_pkg \%hash;
  $record = new FS::quotation_pkg { 'column' => 'value' };

  $error = $record->insert;

  $error = $new_record->replace($old_record);

  $error = $record->delete;

  $error = $record->check;

=head1 DESCRIPTION

An FS::quotation_pkg object represents a quotation package.
FS::quotation_pkg inherits from FS::Record.  The following fields are currently
supported:

=over 4

=item quotationpkgnum

primary key

=item pkgpart

pkgpart (L<FS::part_pkg>) of the package

=item locationnum

locationnum (L<FS::cust_location>) where the package will be in service

=item start_date

expected start date for the package, as a timestamp

=item contract_end

contract end date

=item quantity

quantity

=item waive_setup

'Y' to waive the setup fee

=item unitsetup

The amount per package that will be charged in setup/one-time fees.

=item unitrecur

The amount per package that will be charged per billing cycle.

=item freq

The length of the billing cycle. If zero it's a one-time charge; if any 
other number it's that many months; other values are in L<FS::Misc::pkg_freqs>.

=back

=head1 METHODS

=over 4

=item new HASHREF

Creates a new quotation package.  To add the quotation package to the database,
see L<"insert">.

Note that this stores the hash reference, not a distinct copy of the hash it
points to.  You can ask the object for a copy with the I<hash> method.

=cut

sub table { 'quotation_pkg'; }

sub display_table         { 'quotation_pkg'; }

#forget it, just overriding cust_bill_pkg_display entirely
#sub display_table_orderby { 'quotationpkgnum'; } # something else?
#                                                 #  (for invoice display order)

sub discount_table        { 'quotation_pkg_discount'; }
sub detail_table          { 'quotation_pkg_detail'; }

=item insert

Adds this record to the database.  If there is an error, returns the error,
otherwise returns false.  Accepts the following options:

quotation_details - optional arrayref of detail strings to add (creates quotation_pkg_detail records)

copy_on_order - value for this field when creating quotation_pkg_detail records (same for all details)

=cut

sub insert {
  my ($self, %options) = @_;

  my $dbh = dbh;
  my $oldAutoCommit = $FS::UID::AutoCommit;
  local $FS::UID::AutoCommit = 0;

  #false laziness w/cust_main::Packages::order_pkg
  if ( $options{'locationnum'} and $options{'locationnum'} != -1 ) {

    $self->locationnum($options{'locationnum'});

  } elsif ( $options{'cust_location'} ) {

    my $error = $options{'cust_location'}->find_or_insert;
    if ( $error ) {
      $dbh->rollback if $oldAutoCommit;
      return "inserting cust_location (transaction rolled back): $error";
    }
    $self->locationnum($options{'cust_location'}->locationnum);

  }

  my $error = $self->SUPER::insert;

  if ( !$error and ($self->setup_discountnum || $self->recur_discountnum) ) {
      #warn "inserting discount\n";
    $error = $self->insert_discount;
    $error .= ' (setting discount)' if $error;
  }

  if ( $error ) {
    $dbh->rollback if $oldAutoCommit;
    return $error;
  }

  if ($options{'quotation_details'}) {
    $error = $self->set_details(
                details => $options{'quotation_details'},
                copy_on_order => $options{'copy_on_order'} ? 'Y' : '',
             );
    if ( $error ) {
      $error .= ' (setting details)';
      $dbh->rollback if $oldAutoCommit;
      return $error;
    }
  }

  $dbh->commit if $oldAutoCommit;
  return '';
}

=item delete

Delete this record from the database.

=cut

sub delete {
  my $self = shift;

  my $dbh = dbh;
  my $oldAutoCommit = $FS::UID::AutoCommit;
  local $FS::UID::AutoCommit = 0;

  my $error = $self->delete_details;
  if ( $error ) {
    $dbh->rollback if $oldAutoCommit;
    return $error;
  }

  foreach ($self->quotation_pkg_discount, $self->quotation_pkg_tax) {
    $error = $_->delete;
    if ( $error ) {
      $dbh->rollback if $oldAutoCommit;
      return $error . ' (deleting discount)';
    }
  }

  $error = $self->SUPER::delete;
  if ( $error ) {
    $dbh->rollback if $oldAutoCommit;
    return $error;
  } else {
    $dbh->commit if $oldAutoCommit;
  }
  
  $self->quotation->estimate;
}

=item replace OLD_RECORD

Replaces the OLD_RECORD with this one in the database.  If there is an error,
returns the error, otherwise returns false.

=item check

Checks all fields to make sure this is a valid quotation package.  If there is
an error, returns the error, otherwise returns false.  Called by the insert
and replace methods.

=cut

sub check {
  my $self = shift;

  my @freqs = ('', keys (%{ FS::Misc->pkg_freqs }));

  my $error = 
    $self->ut_numbern('quotationpkgnum')
    || $self->ut_foreign_key(  'quotationnum', 'quotation',    'quotationnum' )
    || $self->ut_foreign_key(  'pkgpart',      'part_pkg',     'pkgpart'      )
    || $self->ut_foreign_keyn( 'locationnum', 'cust_location', 'locationnum'  )
    || $self->ut_numbern('start_date')
    || $self->ut_numbern('contract_end')
    || $self->ut_numbern('quantity')
    || $self->ut_moneyn('unitsetup')
    || $self->ut_moneyn('unitrecur')
    || $self->ut_enum('freq', \@freqs)
    || $self->ut_enum('waive_setup', [ '', 'Y'] )
  ;

  if ($self->locationnum eq '') {
    # use the customer default
    my $quotation = $self->quotation;
    if ($quotation->custnum) {
      $self->set('locationnum', $quotation->cust_main->ship_locationnum);
    } elsif ($quotation->prospectnum) {
      # use the first non-disabled location for that prospect
      my $cust_location = qsearchs('cust_location',
        { prospectnum => $quotation->prospectnum,
          disabled => '' });
      $self->set('locationnum', $cust_location->locationnum) if $cust_location;
    } # else the quotation is invalid
  }

  return $error if $error;

  $self->SUPER::check;
}

#it looks redundant with a v4.x+ auto-generated method, but need to override
# FS::TemplateItem_Mixin's version
sub part_pkg {
  my $self = shift;
  qsearchs('part_pkg', { 'pkgpart' => $self->pkgpart } );
}

sub desc {
  my $self = shift;
  $self->part_pkg->pkg;
}

=cut

=item insert_discount

Associates this package with a discount (see L<FS::cust_pkg_discount>,
possibly inserting a new discount on the fly (see L<FS::discount>). Properties
of the discount will be taken from this object.

=cut

sub insert_discount {
  #my ($self, %options) = @_;
  my $self = shift;

  foreach my $x (qw(setup recur)) {
    if ( my $discountnum = $self->get("${x}_discountnum") ) {
      my $cust_pkg_discount = FS::quotation_pkg_discount->new( { 
        'quotationpkgnum' => $self->quotationpkgnum,
        'discountnum' => $discountnum,
        'setuprecur'  => $x,
        #for the create a new discount case
        'amount'      => $self->get("${x}_discountnum_amount"),
        'percent'     => $self->get("${x}_discountnum_percent"),
        'months'      => $self->get("${x}_discountnum_months"),
      } );
      if ( $x eq 'setup' ) {
        $cust_pkg_discount->setup('Y');
        $cust_pkg_discount->months('');
      } 
      my $error = $cust_pkg_discount->insert;
      return $error if $error;
    } 
  } 
}

sub _item_discount {
  my $self = shift;
  my %options = @_;
  my $setuprecur = $options{'setuprecur'};
  # a little different from cust_bill_pkg::_item_discount, in that this one
  # is asked specifically whether to show setup or recur discounts (because
  # on the quotation they're separate sections entirely)

  my @pkg_discounts = grep { $_->setuprecur eq $setuprecur }
                        $self->pkg_discount;
  return if @pkg_discounts == 0;
  
  my @ext;
  my $d = {
    _is_discount    => 1,
    description     => $self->mt('Discount'),
    amount          => 0,
    ext_description => \@ext,
    # maybe should show quantity/unit discount?
  };
  foreach my $pkg_discount (@pkg_discounts) {
    push @ext, $pkg_discount->description;
    my $amount = $pkg_discount->get('amount');
    $d->{amount} -= $amount;
  }
  $d->{amount} = sprintf('%.2f', $d->{amount} * $self->quantity);
  
  return $d;
}

sub setup {
  my $self = shift;
  return '0.00' if $self->waive_setup eq 'Y';;
  my $discount_amount = sum(0, map { $_->amount }
                               grep { $_->setuprecur eq 'setup' }
                               $self->pkg_discount
                           );
  ($self->unitsetup - $discount_amount) * ($self->quantity || 1);

}

sub setup_show_zero {
  my $self = shift;
  return $self->part_pkg->setup_show_zero;
}

sub setup_tax {
  my $self = shift;
  sum(0, map { $_->setup_amount } $self->quotation_pkg_tax);
}

sub recur {
  my $self = shift;
  my $discount_amount = sum(0, map { $_->amount }
                               grep { $_->setuprecur eq 'recur' }
                               $self->pkg_discount
                           );
  ($self->unitrecur - $discount_amount) * ($self->quantity || 1);

}

sub recur_show_zero {
  my $self = shift;
  return $self->part_pkg->recur_show_zero;
}

sub recur_tax {
  my $self = shift;
  sum(0, map { $_->recur_amount } $self->quotation_pkg_tax);
}

=item part_pkg_currency_option OPTIONNAME

Returns a two item list consisting of the currency of this quotation's customer
or prospect, if any, and a value for the provided option.  If the customer or
prospect has a currency, the value is the option value the given name and the
currency (see L<FS::part_pkg_currency>).  Otherwise, if the customer or
prospect has no currency, is the regular option value for the given name (see
L<FS::part_pkg_option>).

=cut

#false laziness w/cust_pkg->part_pkg_currency_option
sub part_pkg_currency_option {
  my( $self, $optionname ) = @_;
  my $part_pkg = $self->part_pkg;
  my $prospect_or_customer = $self->cust_main || $self->prospect_main;
  if ( my $currency = $prospect_or_customer->currency ) {
    ($currency, $part_pkg->part_pkg_currency_option($currency, $optionname) );
  } else {
    ('', $part_pkg->option($optionname) );
  }
}

=item delete_details

Deletes all quotation_pkgs_details associated with this pkg (see L<FS::quotation_pkg_detail>).

=cut

sub delete_details {
  my $self = shift;

  my $oldAutoCommit = $FS::UID::AutoCommit;
  local $FS::UID::AutoCommit = 0;
  my $dbh = dbh;

  foreach my $detail ( qsearch('quotation_pkg_detail',{ 'quotationpkgnum' => $self->quotationpkgnum }) ) {
    my $error = $detail->delete;
    if ( $error ) {
      $dbh->rollback if $oldAutoCommit;
      return "error removing old detail: $error";
    }
  }

  $dbh->commit or die $dbh->errstr if $oldAutoCommit;
  '';

}

=item set_details PARAM

Sets new quotation details for this package (see L<FS::quotation_pkg_detail>),
removing existing details.

Recognizes the following parameters:

details - arrayref of strings, one for each new detail

copy_on_order - if true, sets copy_on_order flag on new details

If there is an error, returns the error, otherwise returns false.

=cut

sub set_details {
  my $self = shift;
  my %opt = @_;

  $opt{'details'} ||= [];
  my @details = @{$opt{'details'}};

  my $oldAutoCommit = $FS::UID::AutoCommit;
  local $FS::UID::AutoCommit = 0;
  my $dbh = dbh;

  my $error = $self->delete_details;
  if ( $error ) {
    $dbh->rollback if $oldAutoCommit;
    return $error;
  }

  foreach my $detail ( @details ) {
    my $quotation_pkg_detail = new FS::quotation_pkg_detail {
      'quotationpkgnum' => $self->quotationpkgnum,
      'detail' => $detail,
      'copy_on_order' => $opt{'copy_on_order'} ? 'Y' : '',
    };
    $error = $quotation_pkg_detail->insert;
    if ( $error ) {
      $dbh->rollback if $oldAutoCommit;
      return "error adding new detail: $error";
    }
  }

  $dbh->commit or die $dbh->errstr if $oldAutoCommit;
  '';

}

sub details_header {
  return ();
}

=item cust_bill_pkg_display [ type => TYPE ]

=cut

sub cust_bill_pkg_display {
  my ( $self, %opt ) = @_;

  my $type = $opt{type} if exists $opt{type};
  return () if $type eq 'U'; #quotations don't have usage

  if ( $self->get('display') ) {
    return ( grep { defined($type) ? ($type eq $_->type) : 1 }
               @{ $self->get('display') }
           );
  } else {

    #??
    my $setup = $self->new($self->hashref);
    $setup->{'_NO_RECUR_KLUDGE'} = 1;
    $setup->{'type'} = 'S';
    my $recur = $self->new($self->hashref);
    $recur->{'_NO_SETUP_KLUDGE'} = 1;
    $recur->{'type'} = 'R';

    if ( $type eq 'S' ) {
      return ($setup);
    } elsif ( $type eq 'R' ) {
      return ($recur);
    } else {
      #return ($setup, $recur);
      return ($self);
    }

  }

}

=item cust_main

Returns the customer (L<FS::cust_main> object).

=cut

sub cust_main {
  my $self = shift;
  my $quotation = $self->quotation or return '';
  $quotation->cust_main;
}

=item prospect_main

Returns the prospect (L<FS::prospect_main> object).

=cut

sub prospect_main {
  my $self = shift;
  my $quotation = $self->quotation or return '';
  $quotation->prospect_main;
}

sub tax_locationnum {
  my $self = shift;
  $self->locationnum;
}

sub _upgrade_data {
  my $class = shift;
  my @quotation_pkg_without_location =
    qsearch( 'quotation_pkg', { locationnum => '' } );
  if (@quotation_pkg_without_location) {
    warn "setting default location on quotation_pkg records\n";
    foreach my $quotation_pkg (@quotation_pkg_without_location) {
      # check() will fix this
      my $error = $quotation_pkg->replace;
      if ($error) {
        die "quotation #".$quotation_pkg->quotationnum.": $error\n";
      }
    }
  }
  '';
}

=back

=head1 BUGS

Doesn't support fees, or add-on packages.

=head1 SEE ALSO

L<FS::Record>, schema.html from the base documentation.

=cut

1;

