#!/usr/bin/perl -Tw
#
# $Id: part_svc.cgi,v 1.12 1999-04-09 04:22:34 ivan Exp $
#
# ivan@sisd.com 97-nov-14
#
# Changes to allow page to work at a relative position in server
#       bmccane@maxbaud.net     98-apr-3
#
# use FS::CGI, added inline documentation ivan@sisd.com 98-jul-12
#
# $Log: part_svc.cgi,v $
# Revision 1.12  1999-04-09 04:22:34  ivan
# also table()
#
# Revision 1.11  1999/04/09 03:52:55  ivan
# explicit & for table/itable/ntable
#
# Revision 1.10  1999/04/08 13:01:50  ivan
#  [ AND DOCUMENT! ] all svc_acct services should have a default
#  or fixed shell
#
# Revision 1.9  1999/02/23 08:09:21  ivan
# beginnings of one-screen new customer entry and some other miscellania
#
# Revision 1.8  1999/02/07 09:59:21  ivan
# more mod_perl fixes, and bugfixes Peter Wemm sent via email
#
# Revision 1.7  1999/01/19 05:13:42  ivan
# for mod_perl: no more top-level my() variables; use vars instead
# also the last s/create/new/;
#
# Revision 1.6  1999/01/18 09:41:31  ivan
# all $cgi->header calls now include ( '-expires' => 'now' ) for mod_perl
# (good idea anyway)
#
# Revision 1.5  1998/12/30 23:03:21  ivan
# bugfixes; fields isn't exported by derived classes
#
# Revision 1.4  1998/12/17 06:17:07  ivan
# fix double // in relative URLs, s/CGI::Base/CGI/;
#
# Revision 1.3  1998/11/21 06:43:26  ivan
# visual
#

use strict;
use vars qw( $cgi $part_svc $action $query $hashref $p %defs $svcdb );
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use FS::UID qw(cgisuidsetup);
use FS::Record qw(qsearchs fields);
use FS::part_svc;
use FS::CGI qw(header menubar popurl table);

$cgi = new CGI;

&cgisuidsetup($cgi);

if ( $cgi->param('error') ) {
  $part_svc = new FS::part_svc ( {
    map { $_, scalar($cgi->param($_)) } fields('part_svc')
  } );
} elsif ( $cgi->keywords ) {
  my ($query) = $cgi->keywords;
  $query =~ /^(\d+)$/;
  $part_svc=qsearchs('part_svc',{'svcpart'=>$1});
} else { #adding
  $part_svc = new  FS::part_svc {};
}
$action = $part_svc->svcpart ? 'Edit' : 'Add';
$hashref = $part_svc->hashref;

$p = popurl(2);
print $cgi->header( '-expires' => 'now' ), header("$action Service Definition", menubar(
  'Main Menu' => $p,
  'View all services' => "${p}browse/part_svc.cgi",
));

print qq!<FONT SIZE="+1" COLOR="#ff0000">Error: !, $cgi->param('error'),
      "</FONT>"
  if $cgi->param('error');

print '<FORM ACTION="', popurl(1), 'process/part_svc.cgi" METHOD=POST>';

print qq!<INPUT TYPE="hidden" NAME="svcpart" VALUE="$hashref->{svcpart}">!,
      "Service Part #", $hashref->{svcpart} ? $hashref->{svcpart} : "(NEW)";

print <<END;
<PRE>
Service  <INPUT TYPE="text" NAME="svc" VALUE="$hashref->{svc}">
</PRE>
Services are items you offer to your customers.
<UL><LI>svc_acct - Shell accounts, POP mailboxes, SLIP/PPP and ISDN accounts
    <LI>svc_domain - Virtual domains
    <LI>svc_acct_sm - Virtual domain mail aliasing
END
#    <LI>svc_charge - One-time charges (Partially unimplemented)
#    <LI>svc_wo - Work orders (Partially unimplemented)
print <<END;
</UL>
For the selected table, you can give fields default or fixed (unchangable)
values.  For example, a SLIP/PPP account may have a default (or perhaps fixed)
<B>slipip</B> of <B>0.0.0.0</B>, while a POP mailbox will probably have a fixed
blank <B>slipip</B> as well as a fixed shell something like <B>/bin/true</B> or
<B>/usr/bin/passwd</B>.
<BR><BR>
END
print &table(), '<TR><TH>Table<SELECT NAME="svcdb" SIZE=1>',
      map '<OPTION'. ' SELECTED'x($_ eq $hashref->{svcdb}). ">$_\n", qw(
        svc_acct svc_domain svc_acct_sm
      );
      print "</SELECT>";
#  svc_acct svc_domain svc_acct_sm svc_charge svc_wo

print <<END;
</TH><TH>Field</TH>
<TH COLSPAN=2>Modifier</TH></TR>
END

#these might belong somewhere else for other user interfaces 
#pry need to eventually create stuff that's shared amount UIs
%defs = (
  'svc_acct' => {
    'dir'       => 'Home directory',
    'uid'       => 'UID (set to fixed and blank for dial-only)',
    'slipip'    => 'IP address',
    'popnum'    => qq!<A HREF="$p/browse/svc_acct_pop.cgi/">POP number</A>!,
    'username'  => 'Username',
    'quota'     => '(unimplemented)',
    '_password' => 'Password',
    'gid'       => 'GID (when blank, defaults to UID)',
    'shell'     => 'Shell (all service definitions should have a default or fixed shell that is present in the <b>shells</b> configuration file)',
    'finger'    => 'GECOS',
  },
  'svc_domain' => {
    'domain'    => 'Domain',
  },
  'svc_acct_sm' => {
    'domuser'   => 'domuser@virtualdomain.com',
    'domuid'    => 'UID where domuser@virtualdomain.com mail is forwarded',
    'domsvc'    => 'svcnum from svc_domain for virtualdomain.com',
  },
  'svc_charge' => {
    'amount'    => 'amount',
  },
  'svc_wo' => {
    'worker'    => 'Worker',
    '_date'      => 'Date',
  },
);

#  svc_acct svc_domain svc_acct_sm svc_charge svc_wo
foreach $svcdb ( qw(
  svc_acct svc_domain svc_acct_sm
) ) {

  my(@rows)=map { /^${svcdb}__(.*)$/; $1 }
    grep ! /_flag$/,
      grep /^${svcdb}__/,
        fields('part_svc');
  my($rowspan)=scalar(@rows);

  my($ptmp)="<TD ROWSPAN=$rowspan>$svcdb</TD>";
  my($row);
  foreach $row (@rows) {
    my $value = $part_svc->getfield($svcdb. '__'. $row);
    my $flag = $part_svc->getfield($svcdb. '__'. $row. '_flag');
    print "<TR>$ptmp<TD>$row";
    print "- <FONT SIZE=-1>$defs{$svcdb}{$row}</FONT>"
      if defined $defs{$svcdb}{$row};
    print "</TD>";
    print qq!<TD><INPUT TYPE="radio" NAME="${svcdb}__${row}_flag" VALUE=""!.
      ' CHECKED'x($flag eq ''). ">Off</TD>";
    print qq!<TD><INPUT TYPE="radio" NAME="${svcdb}__${row}_flag" VALUE="D"!.
      ' CHECKED'x($flag eq 'D'). ">Default ";
    print qq!<INPUT TYPE="radio" NAME="${svcdb}__${row}_flag" VALUE="F"!.
      ' CHECKED'x($flag eq 'F'). ">Fixed ";
    print qq!<INPUT TYPE="text" NAME="${svcdb}__${row}" VALUE="$value">!,
      "</TD></TR>\n";
    $ptmp='';
  }
}
print "</TABLE>";

print qq!\n<BR><INPUT TYPE="submit" VALUE="!,
      $hashref->{svcpart} ? "Apply changes" : "Add service",
      qq!">!;

print <<END;

    </FORM>
  </BODY>
</HTML>
END

