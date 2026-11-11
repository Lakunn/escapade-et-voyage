<?php
/**
 * Médias :
 * - vidéos YouTube collées seules sur une ligne : lecteur léger (vignette + bouton), YouTube
 *   n'est chargé qu'au clic, en mode « nocookie » (performance et vie privée) ;
 * - schémas SVG autorisés au téléversement pour les administrateurs uniquement (fichiers du dépôt).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

add_filter(
	'embed_oembed_html',
	function ( $html, $url ) {
		if ( ! preg_match( '#(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})#', $url, $m ) ) {
			return $html;
		}
		$id    = $m[1];
		$title = preg_match( '/title="([^"]*)"/', $html, $t ) ? $t[1] : 'Vidéo YouTube';
		return sprintf(
			'<figure class="yt-lite"><button type="button" class="yt-lite-btn" data-yt="%1$s" aria-label="Lire la vidéo : %2$s"><img src="https://i.ytimg.com/vi/%1$s/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"><span class="yt-lite-play" aria-hidden="true"></span></button><figcaption>%2$s · <a href="https://www.youtube.com/watch?v=%1$s" rel="noopener" target="_blank">voir sur YouTube</a></figcaption></figure>',
			esc_attr( $id ),
			esc_html( $title )
		);
	},
	10,
	2
);

add_filter(
	'upload_mimes',
	function ( $mimes ) {
		if ( current_user_can( 'manage_options' ) ) {
			$mimes['svg'] = 'image/svg+xml';
		}
		return $mimes;
	}
);

add_filter(
	'wp_check_filetype_and_ext',
	function ( $data, $file, $filename ) {
		if ( current_user_can( 'manage_options' ) && 'svg' === strtolower( pathinfo( $filename, PATHINFO_EXTENSION ) ) ) {
			$data['ext']  = 'svg';
			$data['type'] = 'image/svg+xml';
		}
		return $data;
	},
	10,
	3
);
