<% include('elements/browse.html',
                'title'           => 'Routers',
                'menubar'         => [ @menubar ],
                'name_singular'   => 'router',
                'query'           => { 'table'     => 'router',
                                       'hashref'   => {},
                                       'extra_sql' => $extra_sql,
                                     },
                'count_query'     => "SELECT count(*) from router $count_sql",
                'header'          => [ @header_fields ],
                'fields'          => [ @fields ],
                'links'           => [ @links ],
                'agent_virt'      => 1,
                'agent_null_right'=> "Broadband global configuration",
                'agent_pos'       => 1,
          )
%>
<%init>

die "access denied"
  unless $FS::CurrentUser::CurrentUser->access_right('Broadband configuration')
  || $FS::CurrentUser::CurrentUser->access_right('Broadband global configuration');

my $p2 = popurl(2);
my $extra_sql = '';

my @menubar = ( 'Add a new router', "${p2}edit/router.cgi" );

if ($cgi->param('hidecustomerrouters') eq '1') {
  $extra_sql = 'WHERE svcnum > 0';
  $cgi->delete('hidecustomerrouters');
  push @menubar, 'Show customer routers', $cgi->self_url();
  $cgi->param('hidecustomerrouters', 1);
} else {
  $cgi->param('hidecustomerrouters', 1);
  push @menubar, 'Hide customer routers', $cgi->self_url();
  $cgi->delete('hidecustomerrouters');
}

my @header_fields = ('Router name', 'Address block(s)', 'IP addressing');
my @fields = ( 'routername',
               sub { join( '<BR>', map { $_->NetAddr } shift->addr_block); },
               sub { shift->manual_addr ? 'Manual' : 'Automatic' },
             );
my @links = ( [ "${p2}edit/router.cgi?", 'routernum' ],
              '',
              '',
            );

foreach (FS::router->virtual_fields_hash) {
  push @header_fields, encode_entities($_->{'label'});
  push @fields, encode_entities($_->{'name'});
  push @links, '';
}

push @header_fields, 'Action';
push @fields, sub { 'Delete' };
push @links, [ "${p}misc/delete-router.html?", 'routernum' ];

my $count_sql = $extra_sql.  ( $extra_sql =~ /WHERE/ ? ' AND' : 'WHERE' ).
  $FS::CurrentUser::CurrentUser->agentnums_sql(
    'null_right' => 'Broadband global configuration',
  );


</%init>
