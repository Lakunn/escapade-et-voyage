<?php
/**
 * Sommaire automatique : ajoute des ancres aux H2/H3 du contenu et les mémorise
 * pour l'affichage dans la colonne latérale.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$GLOBALS['vr_toc'] = array();

add_filter(
	'the_content',
	function ( $html ) {
		if ( ! is_singular() || ! in_the_loop() || ! is_main_query() ) {
			return $html;
		}
		$GLOBALS['vr_toc'] = array();
		$used              = array();

		return preg_replace_callback(
			'#<h([23])([^>]*)>(.*?)</h\1>#is',
			function ( $m ) use ( &$used ) {
				$level = (int) $m[1];
				$attrs = $m[2];
				$inner = $m[3];
				$text  = trim( wp_strip_all_tags( $inner ) );
				if ( '' === $text ) {
					return $m[0];
				}
				if ( preg_match( '/\sid=["\']([^"\']+)["\']/', $attrs, $idm ) ) {
					$id = $idm[1];
				} else {
					$base = sanitize_title( $text );
					$base = '' !== $base ? $base : 'section';
					$id   = $base;
					$i    = 2;
					while ( isset( $used[ $id ] ) ) {
						$id = $base . '-' . $i++;
					}
					$attrs .= ' id="' . esc_attr( $id ) . '"';
				}
				$used[ $id ]         = true;
				$GLOBALS['vr_toc'][] = array(
					'level' => $level,
					'id'    => $id,
					'text'  => $text,
				);
				return '<h' . $level . $attrs . '>' . $inner . '</h' . $level . '>';
			},
			$html
		);
	},
	15
);

/** Nombre de H2 dans le contenu (pour décider d'afficher le sommaire). */
function vr_toc_h2_count( $post = null ) {
	return preg_match_all( '#<h2[\s>]#i', (string) get_post( $post )->post_content );
}

/** Affiche le sommaire (à appeler après the_content()). */
function vr_toc() {
	$items = $GLOBALS['vr_toc'] ?? array();
	if ( count( $items ) < 3 ) {
		return;
	}
	echo '<nav class="toc" aria-label="Sommaire"><details open><summary class="toc-title">Sommaire</summary><ol>';
	foreach ( $items as $item ) {
		printf(
			'<li class="lvl-%d"><a href="#%s">%s</a></li>',
			(int) $item['level'],
			esc_attr( $item['id'] ),
			esc_html( $item['text'] )
		);
	}
	echo '</ol></details></nav>';
}
