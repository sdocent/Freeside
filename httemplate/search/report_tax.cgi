<& /elements/header.html, $report->title &>
<TD ALIGN="right">
Download full results<BR>
as <A HREF="<% $p.'search/report_tax-xls.cgi?'.$cgi->query_string%>">Excel spreadsheet</A>
</TD>

<STYLE type="text/css">
TD.sectionhead {
  background-color: #777777;
  color: #ffffff;
  font-weight: bold;
  text-align: left;
}
.grid TH { background-color: #cccccc; padding: 0px 3px 2px }
.row0 TD { background-color: #eeeeee; padding: 0px 3px 2px; text-align: right}
.row1 TD { background-color: #ffffff; padding: 0px 3px 2px; text-align: right}
TD.rowhead { font-weight: bold; text-align: left; padding: 0px 3px }
.bigmath { font-size: large; font-weight: bold; font: sans-serif; text-align: center }
.total { font-style: italic }
</STYLE>

<& /elements/table-grid.html &>
  <THEAD>
  <TR>
    <TH ROWSPAN=3></TH>
    <TH COLSPAN=6>Sales</TH>
    <TH ROWSPAN=3></TH>
    <TH ROWSPAN=3>Rate</TH>
    <TH ROWSPAN=3></TH>
    <TH ROWSPAN=3>Estimated tax</TH>
    <TH ROWSPAN=3>Tax invoiced</TH>
    <TH ROWSPAN=3></TH>
    <TH ROWSPAN=3>Tax credited</TH>
    <TH ROWSPAN=3></TH>
    <TH ROWSPAN=3>Net tax due</TH>
    <TH ROWSPAN=3></TH>
    <TH ROWSPAN=3>Tax collected</TH>
  </TR>

  <TR>
    <TH ROWSPAN=2>Total</TH>
    <TH ROWSPAN=1>Non-taxable</TH>
    <TH ROWSPAN=1>Non-taxable</TH>
    <TH ROWSPAN=1>Non-taxable</TH>
    <TH ROWSPAN=2>Credited</TH>
    <TH ROWSPAN=2>Taxable</TH>
  </TR>

  <TR STYLE="font-size:small">
    <TH>(tax-exempt customer)</TH>
    <TH>(tax-exempt package)</TH>
    <TH>(monthly exemption)</TH>
  </TR>
  </THEAD>

% my $rownum = 0;
% my $prev_row = { pkgclass => 'DUMMY PKGCLASS' };

  <TBODY>
% foreach my $row (@rows) {
%   # before anything else: if this row's pkgclass is not the same as the 
%   # previous row's, then:
%   if ( $row->{pkgclass} ne $prev_row->{pkgclass} ) {
%     if ( $rownum > 0 ) { # start a new section
%       $rownum = 0;
  </TBODY><TBODY>
%     }
%     if ( $params{breakdown}->{pkgclass} ) { # and caption the new section
  <TR>
    <TD COLSPAN=19 CLASS="sectionhead">
      <% $pkgclass_name{$row->{pkgclass}} %>
    </TD>
  </TR>
%     }
%   } # if $row->{pkgclass} ne ...

%   # construct base links that limit to the tax rates described by this row
%   # cust_bill_pkg.cgi wants a list of specific taxnums (and package class)
%   # cust_credit_bill_pkg.html wants a geographic scope (and package class)
%   my $rowlink = ';taxnum=' . $row->{taxnums};
%   if ( $params{breakdown}->{pkgclass} ) {
%     $rowlink .= ';classnum=' . ($row->{pkgclass} || 0);
% #    $rowregion .= ';classnum=' . ($row->{pkgclass} || 0);
%   }
%
%   if ( $row->{total} ) {
  </TBODY><TBODY CLASS="total">
%   }
  <TR CLASS="row<% $rownum % 2 %>">
%   # Row label
%   # Special: If this report is showing all taxes, link the row label to
%   # the detailed tax report for that taxname/country.
    <TD CLASS="rowhead">
%   if ( $all ) {
%     my $newcgi = CGI->new($cgi);
%     $newcgi->delete('all');
%     $newcgi->param('country', $row->{country});
%     $newcgi->param('taxname', $row->{taxname});
%     $newcgi->param('breakdown', qw(city district));

      <A HREF="<% encode_entities( $newcgi->self_url ) %>">
        <% $row->{label} |h %>
      </A>

%   } else { # on the per-taxname report, just show the label with no link

        <% $row->{label} |h %>

%   }
    </TD>
    <TD>
%   # Total sales
      <A HREF="<% $saleslink . $rowlink %>">
        <% $money_sprintf->( $row->{sales} ) %>
      </A>
    </TD>
%   # Exemptions: customer
    <TD>
      <A HREF="<% $saleslink . $rowlink . ';exempt_cust=Y' %>">
        <% $money_sprintf->( $row->{exempt_cust} ) %>
      </A>
    </TD>
%   # package
    <TD>
      <A HREF="<% $saleslink . $rowlink . ';exempt_pkg=Y' %>">
        <% $money_sprintf->( $row->{exempt_pkg} ) %>
      </A>
    </TD>
%   # monthly (note this uses $exemptlink; it's a completely separate report)
    <TD>
      <A HREF="<% $exemptlink . $rowlink %>">
        <% $money_sprintf->( $row->{exempt_monthly} ) %>
      </A>
    </TD>
%   # credited sales
    <TD>
      <A HREF="<% $salescreditlink . $rowlink %>">
        <% $money_sprintf->( $row->{sales_credited} ) %>
      </A>
    </TD>
%   # taxable sales
    <TD>
      <A HREF="<% $saleslink . $rowlink . ";taxable=1" %>">
        <% $money_sprintf->( $row->{taxable} ) %>
      </A>
    </TD>
    <TD CLASS="bigmath"> &times; </TD>
    <TD><% $row->{rate} %></TD>
%   # estimated tax
    <TD CLASS="bigmath"> = </TD>
    <TD>
%   if ( $row->{estimated} ) {
      <% $money_sprintf->( $row->{estimated} ) %>
%   }
    </TD>
%   # invoiced tax
    <TD>
      <A HREF="<% $taxlink . $rowlink %>">
        <% $money_sprintf->( $row->{tax} ) %>
      </A>
    </TD>
%   # credited tax
    <TD CLASS="bigmath"> &minus; </TD>
    <TD>
%#      <A HREF="<% $creditlink . $rowlink %>"> currently broken
        <% $money_sprintf->( $row->{tax_credited} ) %>
%#      </A>
    </TD>
%   # net tax due
    <TD CLASS="bigmath"> = </TD>
    <TD><% $money_sprintf->( $row->{tax} - $row->{tax_credited} ) %></TD>
%   # tax collected
    <TD>&nbsp;</TD>
    <TD><% $money_sprintf->( $row->{tax_paid} ) %></TD>
  </TR>
%   $rownum++;
%   $prev_row = $row;
% } # foreach my $row
% # at the end of everything
  </TBODY>
% # the all-taxes report doesn't have "out of region"
% if ( !$all and $report->{out_sales} > 0 ) {
  <TBODY CLASS="total" STYLE="background-color: #cccccc; line-height: 3">
    <TR>
      <TD CLASS="rowhead">
        <% emt('Out of taxable region') %>
      </TD>
      <TD STYLE="text-align: right">
        <A HREF="<% $saleslink %>;out=1;taxname=<% encode_entities($params{'taxname'}) %>">
          <% $money_sprintf->( $report->{out_sales} ) %>
        </A>
      </TD>
      <TD COLSPAN=0></TD>
    </TR>
  </TBODY>
% }
</TABLE>

<BR>
<& /elements/table-grid.html &>
  <THEAD>
  <TR>
    <TH ROwSPAN=2></TH>
    <TH ROWSPAN=2>Total credits</TH>
    <TH COLSPAN=3>Applied to</TH>
  </TR>
  <TR STYLE="font-size: small">
    <TH>Taxable sales</TH>
    <TH>Tax-exempt sales</TH>
    <TH>Taxes</TH>
  </TR>
  </THEAD>

% $rownum = 0;
% $prev_row = { pkgclass => 'DUMMY PKGCLASS' };

  <TBODY>
% # mostly duplicates the stuff above...
% # but putting it all in one giant table is no good
% foreach my $row (@rows) {
%   if ( $row->{pkgclass} ne $prev_row->{pkgclass} ) {
%     if ( $rownum > 0 ) { # start a new section
%       $rownum = 0;
  </TBODY><TBODY>
%     }
%     if ( $params{breakdown}->{pkgclass} ) { # and caption the new section
  <TR>
    <TD COLSPAN=5 CLASS="sectionhead">
      <% $pkgclass_name{$row->{pkgclass}} %>
    </TD>
  </TR>
%     }
%   } # if $row->{pkgclass} ne ...

%   my $rowlink = ';taxnum=' . $row->{taxnums};
%
%   if ( $row->{total} ) {
  </TBODY><TBODY CLASS="total">
%   }
  <TR CLASS="row<% $rownum % 2 %>">
    <TD CLASS="rowhead"><% $row->{label} |h %></TD>
    <TD>
%   # Total credits
      <% $money_sprintf->( $row->{credits} ) %>
    </TD>
%   # Credits to taxable sales
    <TD>
      <A HREF="<% $salescreditlink . $rowlink %>">
        <% $money_sprintf->( $row->{sales_credited} ) %>
      </A>
    </TD>
%   # ... to exempt sales (link is the same, it shows both exempt and taxable)
    <TD>
      <A HREF="<% $salescreditlink . $rowlink %>">
        <% $money_sprintf->( $row->{exempt_credited} ) %>
      </A>
    </TD>
%   # ... to taxes
    <TD>
%#      <A HREF="<% $creditlink . $rowlink %>"> currently broken
        <% $money_sprintf->( $row->{tax_credited} ) %>
%#      </A>
    </TD>
  </TR>
%   $rownum++;
%   $prev_row = $row;
% } # foreach my $row
% # "out of taxable region" for credits (there is a need for it)
% if ( !$all and $report->{out_credit} > 0 ) {
%   my $creditlink = "cust_credit_bill_pkg.html?out=1;$dateagentlink";
%   if ( $params{'credit_date'} eq 'cust_credit_bill' ) {
%     $creditlink =~ s/begin/credit_begin/;
%     $creditlink =~ s/end/credit_end/;
%   }
%   $creditlink .= ";taxname=" . encode_entities($params{'taxname'});
  <TBODY CLASS="total" STYLE="background-color: #cccccc; line-height: 3">
    <TR>
      <TD CLASS="rowhead">
        <% emt('Out of taxable region') %>
      </TD>
      <TD STYLE="text-align: right">
        <A HREF="<% $creditlink %>">
          <% $money_sprintf->( $report->{out_credit} ) %>
        </A>
      </TD>
      <TD COLSPAN=0></TD>
    </TR>
  </TBODY>
% }
  </TBODY>
</TABLE>


<& /elements/footer.html &>
<%init>

die "access denied"
  unless $FS::CurrentUser::CurrentUser->access_right('Financial reports');

my $DEBUG = $cgi->param('debug') || 0;

my $conf = new FS::Conf;

my($beginning, $ending) = FS::UI::Web::parse_beginning_ending($cgi);

my %params = (
  beginning => $beginning,
  ending    => $ending,
);
$params{debug}   = $DEBUG;
my $agentname;

# filter by agentnum
if ( $cgi->param('agentnum') =~ /^(\d+)$/ ) {
  my $agent = FS::agent->by_key($1) or die "unknown agentnum $1";
  $params{agentnum} = $1;
  $agentname = $agent->agentname;
}

# credit date behavior: limit by the date of the credit application, or
# the invoice?
if ( $cgi->param('credit_date') eq 'cust_credit_bill' ) {
  $params{credit_date} = 'cust_credit_bill';
} else {
  $params{credit_date} = 'cust_bill';
}

my $all = $cgi->param('all');
my $report_class;

if ( $all ) {
  # then show the master report, no country, no taxname, no breakdown
  $report_class = 'FS::Report::Tax::All';
} else {
  $report_class = 'FS::Report::Tax::ByName';
  $params{country} = $cgi->param('country');
  $params{breakdown} = { map { $_ => 1 } $cgi->param('breakdown') };

  # allow anything in here; FS::Report::Tax will treat it as unsafe
  if ( length($cgi->param('taxname')) ) {
    $params{taxname} = $cgi->param('taxname');
  } else {
    die "taxname required";
  }
}

if ($DEBUG) {
  warn "REPORT: $report_class\nPARAMS:\n".Dumper(\%params)."\n\n";
}

my $report = $report_class->report(%params);
my @rows = $report->table; # array of hashrefs

my $money_char = $conf->config('money_char') || '$';
my $money_sprintf = sub {
  $money_char. sprintf('%.2f', shift);
};

my $dateagentlink = "begin=$beginning;end=$ending";
if ( $params{agentnum} ) {
  $dateagentlink .= ';agentnum=' . $params{agentnum};
}
my $saleslink  = $p. "search/cust_bill_pkg.cgi?$dateagentlink;nottax=1";
my $taxlink    = $p. "search/cust_bill_pkg.cgi?$dateagentlink;istax=1";
my $exemptlink = $p. "search/cust_tax_exempt_pkg.cgi?$dateagentlink";
my $salescreditlink = $p. "search/cust_bill_pkg.cgi?$dateagentlink;nottax=1;credit=1";
if ( $params{'credit_date'} eq 'cust_credit_bill' ) {
  $salescreditlink =~ s/begin/credit_begin/;
  $salescreditlink =~ s/end/credit_end/;
  $saleslink .= ";credit_begin=$beginning;credit_end=$ending";
}
#my $creditlink = $p. "search/cust_bill_pkg.cgi?$dateagentlink;credit=1;istax=1";
#if ( $params{'credit_date'} eq 'cust_credit_bill' ) {
#  $creditlink =~ s/begin/credit_begin/;
#  $creditlink =~ s/end/credit_end/;
#}
my $creditlink = ''; # disabled until we find a sane way to do this

my %pkgclass_name = map { $_->classnum, $_->classname } qsearch('pkg_class');
$pkgclass_name{''} = 'Unclassified';

</%init>
