<?php
/**
 * Données structurées JSON-LD (un seul @graph par page) :
 * WebSite, Person (auteur = éditeur), BlogPosting / WebPage / CollectionPage,
 * BreadcrumbList et FAQPage (si le contenu contient une <section class="faq">).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function vr_schema_person() {
	$home   = home_url( '/' );
	$person = array(
		'@type'    => vr_config( 'publisher_type', 'Person' ),
		'@id'      => $home . '#person',
		'name'     => vr_config( 'author.name', 'Valentin Rouault' ),
		'url'      => home_url( (string) vr_config( 'author.page', '/' ) ),
		'jobTitle' => 'Person' === vr_config( 'publisher_type', 'Person' ) ? vr_config( 'author.role', '' ) : '',
	);
	if ( vr_config( 'author.photo' ) ) {
		$person['image'] = vr_config( 'author.photo' );
	}
	$same_as = array_values( array_filter( wp_list_pluck( (array) vr_config( 'author.links', array() ), 'url' ) ) );
	if ( $same_as ) {
		$person['sameAs'] = $same_as;
	}
	$knows = (array) vr_config( 'author.knows_about', array() );
	if ( $knows ) {
		$person['knowsAbout'] = $knows;
	}
	if ( vr_config( 'author.bio' ) ) {
		$person['description'] = vr_config( 'author.bio' );
	}
	return array_filter( $person );
}

function vr_schema_breadcrumb( array $trail ) {
	$items = array();
	foreach ( array_values( $trail ) as $i => $crumb ) {
		$items[] = array(
			'@type'    => 'ListItem',
			'position' => $i + 1,
			'name'     => $crumb[0],
			'item'     => $crumb[1],
		);
	}
	return array(
		'@type'           => 'BreadcrumbList',
		'@id'             => vr_canonical() . '#breadcrumb',
		'itemListElement' => $items,
	);
}

/** Extrait les paires question / réponse d'une <section class="faq"> (H3 + contenu). */
function vr_schema_faq( $html ) {
	if ( ! preg_match( '#<section[^>]*class="[^"]*\bfaq\b[^"]*"[^>]*>(.*?)</section>#is', $html, $m ) ) {
		return null;
	}
	$parts = preg_split( '#<h3[^>]*>#i', $m[1] );
	array_shift( $parts );
	$qa = array();
	foreach ( $parts as $part ) {
		$split = preg_split( '#</h3>#i', $part, 2 );
		if ( count( $split ) < 2 ) {
			continue;
		}
		$q = trim( wp_strip_all_tags( $split[0] ) );
		$a = trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( $split[1] ) ) );
		if ( $q && $a ) {
			$qa[] = array(
				'@type'          => 'Question',
				'name'           => $q,
				'acceptedAnswer' => array(
					'@type' => 'Answer',
					'text'  => $a,
				),
			);
		}
	}
	if ( ! $qa ) {
		return null;
	}
	return array(
		'@type'      => 'FAQPage',
		'@id'        => vr_canonical() . '#faq',
		'mainEntity' => $qa,
	);
}

add_action(
	'wp_head',
	function () {
		if ( vr_seo_plugin_active() || is_404() || is_search() ) {
			return;
		}
		$home  = home_url( '/' );
		$url   = vr_canonical();
		$graph = array();

		$graph[] = array(
			'@type'           => 'WebSite',
			'@id'             => $home . '#website',
			'url'             => $home,
			'name'            => vr_config( 'brand.name', get_bloginfo( 'name' ) ),
			'description'     => vr_config( 'brand.tagline', get_bloginfo( 'description' ) ),
			'inLanguage'      => 'fr-FR',
			'publisher'       => array( '@id' => $home . '#person' ),
			'potentialAction' => array(
				'@type'       => 'SearchAction',
				'target'      => $home . '?s={search_term_string}',
				'query-input' => 'required name=search_term_string',
			),
		);
		$graph[] = vr_schema_person();

		$crumbs = array( array( 'Accueil', $home ) );

		if ( is_singular( 'post' ) ) {
			$post = get_queried_object();
			$cat  = vr_primary_category( $post );
			$blog = (int) get_option( 'page_for_posts' );
			if ( $blog ) {
				$crumbs[] = array( get_the_title( $blog ), get_permalink( $blog ) );
			}
			if ( $cat ) {
				$crumbs[] = array( $cat->name, get_term_link( $cat ) );
			}
			$crumbs[] = array( get_the_title( $post ), $url );

			$article = array(
				'@type'            => 'BlogPosting',
				'@id'              => $url . '#article',
				'mainEntityOfPage' => $url,
				'headline'         => wp_strip_all_tags( get_the_title( $post ) ),
				'description'      => vr_meta_description(),
				'datePublished'    => get_the_date( DATE_W3C, $post ),
				'dateModified'     => get_the_modified_date( DATE_W3C, $post ),
				'author'           => array( '@id' => $home . '#person' ),
				'publisher'        => array( '@id' => $home . '#person' ),
				'isPartOf'         => array( '@id' => $home . '#website' ),
				'inLanguage'       => 'fr-FR',
				'wordCount'        => str_word_count( wp_strip_all_tags( $post->post_content ) ),
				'breadcrumb'       => array( '@id' => $url . '#breadcrumb' ),
			);
			if ( $cat ) {
				$article['articleSection'] = $cat->name;
			}
			$essentiel = vr_essentiel( $post );
			if ( $essentiel ) {
				$article['abstract'] = implode( ' ', $essentiel );
			}
			if ( has_post_thumbnail( $post ) ) {
				$article['image'] = get_the_post_thumbnail_url( $post, 'vr-cover' );
			}
			$graph[] = $article;
			$faq     = vr_schema_faq( $post->post_content );
			if ( $faq ) {
				$graph[] = $faq;
			}
		} elseif ( is_page() && ! is_front_page() ) {
			$post     = get_queried_object();
			$crumbs[] = array( get_the_title( $post ), $url );
			$graph[]  = array(
				'@type'         => 'WebPage',
				'@id'           => $url . '#webpage',
				'url'           => $url,
				'name'          => wp_strip_all_tags( get_the_title( $post ) ),
				'description'   => vr_meta_description(),
				'datePublished' => get_the_date( DATE_W3C, $post ),
				'dateModified'  => get_the_modified_date( DATE_W3C, $post ),
				'isPartOf'      => array( '@id' => $home . '#website' ),
				'author'        => array( '@id' => $home . '#person' ),
				'inLanguage'    => 'fr-FR',
				'breadcrumb'    => array( '@id' => $url . '#breadcrumb' ),
			);
			$faq = vr_schema_faq( $post->post_content );
			if ( $faq ) {
				$graph[] = $faq;
			}
		} elseif ( is_home() || is_category() || is_author() ) {
			$name = is_home() ? get_the_title( (int) get_option( 'page_for_posts' ) ) : wp_strip_all_tags( get_the_archive_title() );
			if ( is_category() ) {
				$blog = (int) get_option( 'page_for_posts' );
				if ( $blog ) {
					$crumbs[] = array( get_the_title( $blog ), get_permalink( $blog ) );
				}
			}
			$crumbs[] = array( $name, $url );
			$graph[]  = array(
				'@type'      => is_author() ? 'ProfilePage' : 'CollectionPage',
				'@id'        => $url . '#webpage',
				'url'        => $url,
				'name'       => $name,
				'isPartOf'   => array( '@id' => $home . '#website' ),
				'inLanguage' => 'fr-FR',
				'breadcrumb' => array( '@id' => $url . '#breadcrumb' ),
			);
		}

		if ( count( $crumbs ) > 1 ) {
			$graph[] = vr_schema_breadcrumb( $crumbs );
		}

		echo '<script type="application/ld+json">' . wp_json_encode(
			array(
				'@context' => 'https://schema.org',
				'@graph'   => $graph,
			),
			JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE
		) . "</script>\n";
	},
	5
);
