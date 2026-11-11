<!doctype html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<a class="skip-link" href="#contenu">Aller au contenu</a>
<header class="site-header">
	<div class="wrap masthead">
		<a class="brand" href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home">
			<span class="brand-name"><?php echo esc_html( vr_config( 'brand.name', get_bloginfo( 'name' ) ) ); ?></span>
			<span class="brand-tag"><?php echo esc_html( vr_config( 'brand.tagline', get_bloginfo( 'description' ) ) ); ?></span>
		</a>
		<button class="nav-toggle" aria-expanded="false" aria-controls="primary-nav">Menu</button>
		<nav id="primary-nav" class="primary-nav" aria-label="Navigation principale">
			<?php vr_nav( 'nav' ); ?>
		</nav>
		<form class="header-search" role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>">
			<label class="screen-reader-text" for="hs">Rechercher</label>
			<input id="hs" type="search" name="s" placeholder="Rechercher…" value="<?php echo esc_attr( get_search_query() ); ?>">
		</form>
	</div>
	<?php
	$vr_ticker = get_posts(
		array(
			'posts_per_page'      => 4,
			'ignore_sticky_posts' => true,
		)
	);
	if ( $vr_ticker ) :
		?>
	<div class="ticker"><div class="wrap">
		<strong>Derniers articles</strong>
		<?php foreach ( $vr_ticker as $vr_p ) : ?>
			<a href="<?php echo esc_url( get_permalink( $vr_p ) ); ?>"><?php echo esc_html( get_the_title( $vr_p ) ); ?></a>
		<?php endforeach; ?>
	</div></div>
	<?php endif; ?>
</header>
<main id="contenu">
