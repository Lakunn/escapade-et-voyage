<?php
/**
 * VR Média — fonctions du thème.
 *
 * Le thème est piloté depuis le dépôt git :
 * - la configuration (marque, menus, rubriques, auteur, newsletter) vient de site.json,
 *   généré par le workflow de déploiement à partir de config/site.yml ;
 * - les contenus sont poussés par l'API REST avec leurs métadonnées SEO (vr_*).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'VR_VERSION', '1.0.0' );
define( 'VR_DIR', get_template_directory() );
define( 'VR_URI', get_template_directory_uri() );

/**
 * Configuration du site (site.json, généré depuis config/site.yml).
 */
function vr_config( $key = null, $default = null ) {
	static $config = null;
	if ( null === $config ) {
		$config = array();
		$file   = VR_DIR . '/site.json';
		if ( is_readable( $file ) ) {
			$decoded = json_decode( (string) file_get_contents( $file ), true );
			if ( is_array( $decoded ) ) {
				$config = $decoded;
			}
		}
	}
	if ( null === $key ) {
		return $config;
	}
	$value = $config;
	foreach ( explode( '.', $key ) as $part ) {
		if ( ! is_array( $value ) || ! array_key_exists( $part, $value ) ) {
			return $default;
		}
		$value = $value[ $part ];
	}
	return $value;
}

/**
 * Un plugin SEO gère-t-il déjà le <head> ? Dans ce cas, le thème se retire.
 */
function vr_seo_plugin_active() {
	return defined( 'WPSEO_VERSION' ) || class_exists( 'RankMath' ) || defined( 'AIOSEO_VERSION' ) || defined( 'SEOPRESS_VERSION' ) || defined( 'THE_SEO_FRAMEWORK_VERSION' );
}

require VR_DIR . '/inc/toc.php';
require VR_DIR . '/inc/seo.php';
require VR_DIR . '/inc/schema.php';
require VR_DIR . '/inc/llms.php';
require VR_DIR . '/inc/consent.php';
require VR_DIR . '/inc/media.php';
require VR_DIR . '/inc/tools.php';

/* ---------------------------------------------------------------------------
 * Setup
 * ------------------------------------------------------------------------ */
add_action(
	'after_setup_theme',
	function () {
		add_theme_support( 'title-tag' );
		add_theme_support( 'post-thumbnails' );
		add_theme_support( 'automatic-feed-links' );
		add_theme_support( 'responsive-embeds' );
		add_theme_support( 'html5', array( 'search-form', 'gallery', 'caption', 'style', 'script', 'navigation-widgets' ) );
		add_image_size( 'vr-card', 800, 450, true );
		add_image_size( 'vr-cover', 1600, 900, true );
		register_nav_menus(
			array(
				'primary' => 'Menu principal (secours si site.json absent)',
			)
		);
	}
);

/* ---------------------------------------------------------------------------
 * Métadonnées pilotées depuis git (exposées à l'API REST)
 * ------------------------------------------------------------------------ */
add_action(
	'init',
	function () {
		$fields = array(
			'vr_seo_title'        => 'string',
			'vr_meta_description' => 'string',
			'vr_essentiel'        => 'string',
			'vr_source_hash'      => 'string',
			'vr_canonical'        => 'string',
			'vr_noindex'          => 'boolean',
		);
		foreach ( array( 'post', 'page' ) as $type ) {
			foreach ( $fields as $key => $kind ) {
				register_post_meta(
					$type,
					$key,
					array(
						'type'          => $kind,
						'single'        => true,
						'show_in_rest'  => true,
						'auth_callback' => function () {
							return current_user_can( 'edit_posts' );
						},
					)
				);
			}
		}
	}
);

/* ---------------------------------------------------------------------------
 * Assets
 * ------------------------------------------------------------------------ */
add_action(
	'wp_enqueue_scripts',
	function () {
		wp_enqueue_style( 'vr-media', get_stylesheet_uri(), array(), (string) filemtime( VR_DIR . '/style.css' ) );
		wp_enqueue_script( 'vr-media', VR_URI . '/assets/site.js', array(), (string) filemtime( VR_DIR . '/assets/site.js' ), array( 'strategy' => 'defer', 'in_footer' => true ) );

		// Le contenu est du HTML propre : pas besoin des styles de blocs sur le front.
		wp_dequeue_style( 'wp-block-library' );
		wp_dequeue_style( 'wp-block-library-theme' );
		wp_dequeue_style( 'global-styles' );
		wp_dequeue_style( 'classic-theme-styles' );
	},
	20
);

/* ---------------------------------------------------------------------------
 * Nettoyage du <head>
 * ------------------------------------------------------------------------ */
remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
remove_action( 'wp_print_styles', 'print_emoji_styles' );
remove_action( 'wp_head', 'wp_generator' );
remove_action( 'wp_head', 'rsd_link' );
remove_action( 'wp_head', 'wlwmanifest_link' );
remove_action( 'wp_head', 'wp_shortlink_wp_head' );
add_filter( 'the_generator', '__return_empty_string' );

/* ---------------------------------------------------------------------------
 * Helpers de templates
 * ------------------------------------------------------------------------ */

/** Temps de lecture estimé (minutes). */
function vr_reading_time( $post = null ) {
	$post  = get_post( $post );
	$words = str_word_count( wp_strip_all_tags( (string) $post->post_content ), 0, 'àâäéèêëïîôöùûüÿçœæÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇŒÆ' );
	return max( 1, (int) round( $words / 220 ) );
}

/** Rubrique principale d'un article. */
function vr_primary_category( $post = null ) {
	$cats = get_the_category( get_post( $post )->ID );
	if ( empty( $cats ) ) {
		return null;
	}
	// Respecte l'ordre des rubriques défini dans la config.
	$order = wp_list_pluck( (array) vr_config( 'categories', array() ), 'slug' );
	usort(
		$cats,
		function ( $a, $b ) use ( $order ) {
			$ia = array_search( $a->slug, $order, true );
			$ib = array_search( $b->slug, $order, true );
			$ia = false === $ia ? 99 : $ia;
			$ib = false === $ib ? 99 : $ib;
			return $ia <=> $ib;
		}
	);
	return $cats[0];
}

/** Date de mise à jour significative (> 1 jour après publication). */
function vr_was_updated( $post = null ) {
	$post = get_post( $post );
	return ( get_post_modified_time( 'U', true, $post ) - get_post_time( 'U', true, $post ) ) > DAY_IN_SECONDS;
}

/** Points clés « L'essentiel » (une ligne = un point). */
function vr_essentiel( $post = null ) {
	$raw = (string) get_post_meta( get_post( $post )->ID, 'vr_essentiel', true );
	return array_values( array_filter( array_map( 'trim', preg_split( '/\R/', $raw ) ) ) );
}

/** Menu de navigation depuis site.json (ou menu WP en secours). */
function vr_nav( $location = 'nav' ) {
	$items = (array) vr_config( $location, array() );
	if ( empty( $items ) ) {
		if ( 'nav' === $location && has_nav_menu( 'primary' ) ) {
			wp_nav_menu(
				array(
					'theme_location' => 'primary',
					'container'      => false,
				)
			);
		}
		return;
	}
	$current = trailingslashit( strtok( home_url( add_query_arg( array() ) ), '?' ) );
	echo '<ul>';
	foreach ( $items as $item ) {
		$url    = isset( $item['url'] ) ? home_url( $item['url'] ) : '#';
		$active = trailingslashit( $url ) === $current;
		printf(
			'<li%s><a href="%s"%s>%s</a></li>',
			$active ? ' class="current"' : '',
			esc_url( $url ),
			$active ? ' aria-current="page"' : '',
			esc_html( $item['label'] ?? '' )
		);
	}
	echo '</ul>';
}

/** Initiale décorative pour les cartes sans image. */
function vr_initial( $title ) {
	$title = trim( wp_strip_all_tags( $title ) );
	return function_exists( 'mb_substr' ) ? mb_strtoupper( mb_substr( $title, 0, 1 ) ) : strtoupper( substr( $title, 0, 1 ) );
}

/* ---------------------------------------------------------------------------
 * Contenu
 * ------------------------------------------------------------------------ */

// Tableaux scrollables sur mobile.
add_filter(
	'the_content',
	function ( $html ) {
		return preg_replace( '#<table(.*?)</table>#is', '<div class="table-wrap"><table$1</table></div>', $html );
	},
	30
);

add_filter(
	'excerpt_length',
	function () {
		return 28;
	}
);
add_filter(
	'excerpt_more',
	function () {
		return '…';
	}
);

/*
 * Articles par page. ATTENTION : les URL paginées existantes (/blog-seo/page/4/,
 * /category/contenu-seo/page/2/…) font partie du référentiel urls.csv. Des valeurs trop
 * hautes feraient disparaître des pages d'archive : le contrôle post-déploiement échouerait.
 */
add_action(
	'pre_get_posts',
	function ( $q ) {
		if ( is_admin() || ! $q->is_main_query() ) {
			return;
		}
		if ( $q->is_home() ) {
			$q->set( 'posts_per_page', (int) vr_config( 'per_page.blog', 9 ) );
		} elseif ( $q->is_author() ) {
			$q->set( 'posts_per_page', (int) vr_config( 'per_page.author', 5 ) );
		} elseif ( $q->is_category() || $q->is_search() ) {
			$q->set( 'posts_per_page', (int) vr_config( 'per_page.archive', 6 ) );
		}
	}
);

// Un shortcode seul sur sa ligne ne doit pas être enveloppé dans un paragraphe.
add_filter(
	'the_content',
	function ( $html ) {
		return preg_replace( '#<p>\s*(\[gc_[a-z]+\])\s*</p>#', '$1', $html );
	},
	9
);

/** Vide le cache de page (LiteSpeed) quand le thème change, pour servir la nouvelle feuille de style. */
add_action(
	'init',
	function () {
		$vr_rev = '';
		foreach ( array( '/style.css', '/assets/site.js', '/assets/tools.js' ) as $vr_f ) {
			$vr_rev .= file_exists( VR_DIR . $vr_f ) ? filemtime( VR_DIR . $vr_f ) . '-' : '';
		}
		if ( get_option( 'vr_theme_rev' ) === $vr_rev ) {
			return;
		}
		update_option( 'vr_theme_rev', $vr_rev, true );
		do_action( 'litespeed_purge_all' );
		if ( ! headers_sent() ) {
			header( 'X-LiteSpeed-Purge: *' );
		}
	}
);
