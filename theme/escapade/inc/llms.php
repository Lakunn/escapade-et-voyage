<?php
/**
 * /llms.txt : index Markdown du média pour les moteurs génératifs (https://llmstxt.org).
 * Servi dynamiquement, toujours à jour avec les contenus publiés.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

add_action(
	'init',
	function () {
		add_rewrite_rule( '^llms\.txt$', 'index.php?vr_llms=1', 'top' );
		// Re-génère les règles une seule fois par version du thème.
		if ( get_option( 'vr_rewrite_version' ) !== VR_VERSION ) {
			flush_rewrite_rules( false );
			update_option( 'vr_rewrite_version', VR_VERSION );
		}
	}
);

add_filter(
	'query_vars',
	function ( $vars ) {
		$vars[] = 'vr_llms';
		return $vars;
	}
);

// Pas de redirection canonique (ajout de slash) sur /llms.txt.
add_filter(
	'redirect_canonical',
	function ( $redirect ) {
		return get_query_var( 'vr_llms' ) ? false : $redirect;
	}
);

add_action(
	'template_redirect',
	function () {
		if ( ! get_query_var( 'vr_llms' ) ) {
			return;
		}
		$lines   = array();
		$lines[] = '# ' . vr_config( 'brand.name', get_bloginfo( 'name' ) );
		$lines[] = '';
		$lines[] = '> ' . vr_config( 'brand.tagline', get_bloginfo( 'description' ) );
		$lines[] = '';
		if ( vr_config( 'author.bio' ) ) {
			$lines[] = 'Auteur : ' . vr_config( 'author.name' ) . ' — ' . vr_config( 'author.bio' );
			$lines[] = '';
		}

		$lines[] = '## Guides de référence';
		foreach ( get_pages( array( 'sort_column' => 'menu_order' ) ) as $page ) {
			if ( get_post_meta( $page->ID, 'vr_noindex', true ) || (int) get_option( 'page_on_front' ) === $page->ID ) {
				continue;
			}
			$desc    = (string) get_post_meta( $page->ID, 'vr_meta_description', true );
			$lines[] = sprintf( '- [%s](%s)%s', html_entity_decode( get_the_title( $page ), ENT_QUOTES, 'UTF-8' ), get_permalink( $page ), $desc ? ': ' . $desc : '' );
		}
		$lines[] = '';

		foreach ( (array) vr_config( 'categories', array() ) as $conf ) {
			$term = get_category_by_slug( $conf['slug'] ?? '' );
			if ( ! $term ) {
				continue;
			}
			$posts = get_posts(
				array(
					'category'       => $term->term_id,
					'posts_per_page' => 50,
					'orderby'        => 'modified',
				)
			);
			if ( ! $posts ) {
				continue;
			}
			$lines[] = '## ' . html_entity_decode( $term->name, ENT_QUOTES, 'UTF-8' );
			foreach ( $posts as $p ) {
				if ( get_post_meta( $p->ID, 'vr_canonical', true ) ) {
					continue;
				}
				$desc    = (string) get_post_meta( $p->ID, 'vr_meta_description', true );
				$lines[] = sprintf( '- [%s](%s)%s', html_entity_decode( get_the_title( $p ), ENT_QUOTES, 'UTF-8' ), get_permalink( $p ), $desc ? ': ' . $desc : '' );
			}
			$lines[] = '';
		}

		status_header( 200 );
		header( 'Content-Type: text/plain; charset=utf-8' );
		header( 'X-Robots-Tag: noindex' );
		echo implode( "\n", $lines );
		exit;
	}
);
