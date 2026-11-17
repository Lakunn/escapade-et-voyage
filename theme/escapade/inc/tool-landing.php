<?php
/**
 * Pages d'outil traitées comme des landing pages : promesse, mode d'emploi en 3 étapes et outil
 * visibles sans défiler ; l'explication détaillée, la méthode et la FAQ viennent ensuite.
 *
 * Une page est une page d'outil dès que son contenu contient un shortcode d'outil seul sur sa ligne
 * ([ev_…], [gc_…], [vr_…]). Les étapes viennent du champ `tool_steps` du front matter (méta vr_tool_steps),
 * les badges de `tool_chips` (méta vr_tool_chips), avec des valeurs par défaut.
 */

/** Shortcode d'outil de la page courante (premier trouvé), ou chaîne vide. */
function vr_tool_shortcode( $post = null ) {
	$content = (string) get_post_field( 'post_content', get_post( $post ) );
	if ( preg_match( '/^\s*(?:<p>)?(\[(?:ev|gc|vr)_[a-z_]+[^\]]*\])(?:<\/p>)?\s*$/m', $content, $m ) ) {
		$tag = preg_replace( '/^\[([a-z_]+).*$/s', '$1', $m[1] );
		if ( shortcode_exists( $tag ) ) {
			return $m[1];
		}
	}
	return '';
}

/** Lignes d'une méta multi-lignes. */
function vr_meta_lines( $key, $post = null ) {
	$raw = (string) get_post_meta( get_post( $post )->ID, $key, true );
	return array_values( array_filter( array_map( 'trim', preg_split( '/\R/', $raw ) ) ) );
}

/** Contenu de la page sans le shortcode d'outil (déjà affiché dans l'en-tête). */
function vr_tool_rest_content( $shortcode ) {
	$content = str_replace( $shortcode, '', (string) get_the_content() );
	return apply_filters( 'the_content', $content );
}

/** En-tête de landing : texte à gauche, outil à droite (outil juste sous la promesse sur mobile). */
function vr_tool_hero( $shortcode ) {
	$steps = vr_meta_lines( 'vr_tool_steps' );
	if ( ! $steps ) {
		$steps = array( 'Renseignez les champs', 'Lancez le calcul', 'Lisez le résultat et nos conseils' );
	}
	$chips = vr_meta_lines( 'vr_tool_chips' );
	if ( ! $chips ) {
		$chips = array( 'Gratuit', 'Sans inscription', 'Résultat immédiat' );
	}
	$allowed = array( 'strong' => array(), 'em' => array(), 'code' => array() );
	?>
	<header class="tool-hero">
		<div class="tool-hero__pitch">
			<span class="kicker tool-hero__kicker">Outil gratuit</span>
			<h1><?php the_title(); ?></h1>
			<?php if ( has_excerpt() ) : ?>
				<p class="tool-hero__promise"><?php echo esc_html( get_the_excerpt() ); ?></p>
			<?php endif; ?>
			<ul class="tool-hero__chips" aria-label="En bref">
				<?php foreach ( $chips as $chip ) : ?>
					<li><?php echo esc_html( $chip ); ?></li>
				<?php endforeach; ?>
			</ul>
		</div>
		<div class="tool-hero__tool" id="outil">
			<?php echo do_shortcode( $shortcode ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
		</div>
		<ol class="tool-hero__steps" aria-label="Comment ça marche">
			<?php foreach ( array_slice( $steps, 0, 3 ) as $i => $step ) : ?>
				<li><span class="tool-hero__n"><?php echo (int) $i + 1; ?></span><span><?php echo wp_kses( $step, $allowed ); ?></span></li>
			<?php endforeach; ?>
		</ol>
	</header>
	<?php
}
