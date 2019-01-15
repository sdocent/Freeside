package FS::part_event::Action::cust_bill_print_pdf;

use strict;
use base qw( FS::part_event::Action );

sub description { 'Send invoice (spool PDF only)'; }

## declaring that this action will send out an invoice
sub will_send_invoice { 1; }

sub eventtable_hashref {
  { 'cust_bill' => 1 };
}

sub option_fields {
  (
    'modenum' => {  label => 'Invoice mode',
                    type  => 'select-invoice_mode'
                 },
  );
}

sub default_weight { 51; }

sub do_action {
  my( $self, $cust_bill ) = @_;

  #my $cust_main = $self->cust_main($cust_bill);
  #my $cust_main = $cust_bill->cust_main;

  my $opt = { $self->options };
  $opt->{'notice_name'} ||= 'Invoice';

  $cust_bill->set('mode' => $self->option('modenum'));
  $cust_bill->batch_invoice($opt);
}

1;
