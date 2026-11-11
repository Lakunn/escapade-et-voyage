<?php
/**
 * Balises SEO du <head> : title, meta description, canonical, robots, Open Graph.
 * Tout est piloté par les champs vr_* (poussés depuis git) et par site.json.
 * Si un plugin SEO est actif, le thème n'émet rien pour éviter les doublons.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Configuration d'une rubrique (site.json > categories). */
function vr_category_config( $slug ) {
	foreach ( (array) vr_config( 'categories', array() ) as $cat ) {
		if ( ( $cat['slug'] ?? '' ) === $slug ) {
			return $cat;
		}
	}
	return array();
}

/** Numéro de page courant (archives paginées). */
function vr_paged() {
	return max( 1, (int) get_query_var( 'paged' ), (int) get_query_var( 'page' ) );
}

/** Meta description de la page courante. */
function vr_meta_description() {
	$desc = '';
	if ( is_front_page() ) {
		$desc = (string) vr_config( 'home.meta_description', get_bloginfo( 'description' ) );
	} elseif ( is_home() ) {
		$id   = (int) get_option( 'page_for_posts' );
		$desc = (string) get_post_meta( $id, 'vr_meta_description', true );
	} elseif ( is_singular() ) {
		$post = get_queried_object();
		$desc = (string) get_post_meta( $post->ID, 'vr_meta_description', true );
		if ( '' === $desc ) {
			$desc = has_excerpt( $post ) ? get_the_excerpt( $post ) : wp_trim_words( wp_strip_all_tags( $post->post_content ), 28, '…' );
		}
	} elseif ( is_category() ) {
		$term = get_queried_object();
		$conf = vr_category_config( $term->slug );
		$desc = (string) ( $conf['meta_description'] ?? wp_strip_all_tags( term_description( $term ) ) );
	} elseif ( is_author() ) {
		$desc = (string) vr_config( 'author.bio', '' );
	}
	$desc = trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( $desc ) ) );
	if ( '' !== $desc && vr_paged() > 1 ) {
		$desc = sprintf( 'Page %d – %s', vr_paged(), $desc );
	}
	return $desc;
}

/** URL canonique de la page courante. */
function vr_canonical() {
	$paged = vr_paged();
	$url   = '';
	if ( is_front_page() ) {
		$url = home_url( '/' );
	} elseif ( is_home() ) {
		$url = get_permalink( (int) get_option( 'page_for_posts' ) );
	} elseif ( is_singular() ) {
		// Canonical déclarée depuis git (doublon consolidé vers une autre URL, sans redirection).
		$custom = (string) get_post_meta( get_queried_object_id(), 'vr_canonical', true );
		$url    = '' !== $custom ? home_url( $custom ) : get_permalink( get_queried_object() );
	} elseif ( is_category() || is_tag() || is_tax() ) {
		$url = get_term_link( get_queried_object() );
	} elseif ( is_author() ) {
		$url = get_author_posts_url( get_queried_object_id() );
	}
	if ( ! $url || is_wp_error( $url ) ) {
		return '';
	}
	if ( $paged > 1 && ! is_singular() ) {
		$url = trailingslashit( $url ) . user_trailingslashit( 'page/' . $paged, 'paged' );
	}
	return $url;
}

/** Image de partage. */
function vr_share_image() {
	if ( is_singular() && has_post_thumbnail() ) {
		$img = wp_get_attachment_image_src( get_post_thumbnail_id(), 'vr-cover' );
		if ( $img ) {
			return $img[0];
		}
	}
	return (string) vr_config( 'default_share_image', '' );
}

/* -- <title> ------------------------------------------------------------- */
add_filter(
	'pre_get_document_title',
	function ( $title ) {
		if ( vr_seo_plugin_active() ) {
			return $title;
		}
		$custom = '';
		if ( is_front_page() ) {
			$custom = (string) vr_config( 'home.seo_title', '' );
		} elseif ( is_home() ) {
			$custom = (string) get_post_meta( (int) get_option( 'page_for_posts' ), 'vr_seo_title', true );
		} elseif ( is_singular() ) {
			$custom = (string) get_post_meta( get_queried_object_id(), 'vr_seo_title', true );
		} elseif ( is_category() ) {
			$conf   = vr_category_config( get_queried_object()->slug );
			$custom = (string) ( $conf['seo_title'] ?? '' );
		}
		if ( '' === $custom ) {
			return $title;
		}
		if ( vr_paged() > 1 && ! is_singular() ) {
			$custom .= ' – page ' . vr_paged();
		}
		return $custom;
	}
);
add_filter(
	'document_title_separator',
	function () {
		return '|';
	}
);

/* -- robots --------------------------------------------------------------- */
add_filter(
	'wp_robots',
	function ( $robots ) {
		if ( is_search() || is_404() || ( is_singular() && get_post_meta( get_queried_object_id(), 'vr_noindex', true ) ) ) {
			$robots['noindex'] = true;
			$robots['follow']  = true;
			unset( $robots['max-image-preview'] );
		}
		return $robots;
	}
);

/* -- meta, canonical, Open Graph ---------------------------------------- */
remove_action( 'wp_head', 'rel_canonical' );

add_action(
	'wp_head',
	function () {
		if ( vr_seo_plugin_active() ) {
			return; // L'extension SEO gère canonical et meta : pas de doublon.
		}
		$desc      = vr_meta_description();
		$canonical = vr_canonical();
		$image     = vr_share_image();
		$title     = wp_get_document_title();

		if ( $desc ) {
			printf( "<meta name=\"description\" content=\"%s\">\n", esc_attr( $desc ) );
		}
		if ( $canonical && ! is_search() && ! is_404() ) {
			printf( "<link rel=\"canonical\" href=\"%s\">\n", esc_url( $canonical ) );
		}

		$og = array(
			'og:locale'    => 'fr_FR',
			'og:site_name' => vr_config( 'brand.name', get_bloginfo( 'name' ) ),
			'og:type'      => is_singular( 'post' ) ? 'article' : 'website',
			'og:title'     => $title,
			'og:url'       => $canonical,
		);
		if ( $desc ) {
			$og['og:description'] = $desc;
		}
		if ( $image ) {
			$og['og:image'] = $image;
		}
		foreach ( $og as $prop => $val ) {
			if ( $val ) {
				printf( "<meta property=\"%s\" content=\"%s\">\n", esc_attr( $prop ), esc_attr( $val ) );
			}
		}
		if ( is_singular( 'post' ) ) {
			printf( "<meta property=\"article:published_time\" content=\"%s\">\n", esc_attr( get_the_date( DATE_W3C ) ) );
			printf( "<meta property=\"article:modified_time\" content=\"%s\">\n", esc_attr( get_the_modified_date( DATE_W3C ) ) );
		}
		echo "<meta name=\"twitter:card\" content=\"summary_large_image\">\n";
	},
	1
);

/** Les contenus dont la canonical pointe ailleurs sortent du sitemap. */
add_filter(
	'wp_sitemaps_posts_query_args',
	function ( $args ) {
		$args['meta_query'] = array(
			'relation' => 'OR',
			array( 'key' => 'vr_canonical', 'compare' => 'NOT EXISTS' ),
			array( 'key' => 'vr_canonical', 'value' => '' ),
		);
		return $args;
	}
);

/*
 * Lancement progressif : tant qu'une extension SEO (Yoast, Rank Math) reste active pour les contenus importés,
 * les contenus publiés depuis git imposent leur titre, leur description et leur canonical à l'extension.
 */
function vr_git_meta( $key ) {
	if ( ! is_singular() ) {
		return '';
	}
	return (string) get_post_meta( get_queried_object_id(), $key, true );
}
foreach ( array( 'wpseo_title', 'rank_math/frontend/title', 'wpseo_opengraph_title', 'rank_math/opengraph/facebook/og_title' ) as $vr_hook ) {
	add_filter( $vr_hook, function ( $v ) { $t = vr_git_meta( 'vr_seo_title' ); return '' !== $t ? $t : $v; }, 99 );
}
foreach ( array( 'wpseo_metadesc', 'rank_math/frontend/description', 'wpseo_opengraph_desc', 'rank_math/opengraph/facebook/og_description' ) as $vr_hook ) {
	add_filter( $vr_hook, function ( $v ) { $d = vr_git_meta( 'vr_meta_description' ); return '' !== $d ? $d : $v; }, 99 );
}
foreach ( array( 'wpseo_canonical', 'rank_math/frontend/canonical' ) as $vr_hook ) {
	add_filter( $vr_hook, function ( $v ) { $c = vr_git_meta( 'vr_canonical' ); return '' !== $c ? home_url( $c ) : $v; }, 99 );
}
add_filter(
	'pre_get_document_title',
	function ( $title ) {
		$t = vr_git_meta( 'vr_seo_title' );
		return ( vr_seo_plugin_active() && '' !== $t ) ? $t : $title;
	},
	999
);
