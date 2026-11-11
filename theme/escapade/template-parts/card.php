<?php
/**
 * Carte d'article. Arguments : show_media (bool), show_excerpt (bool), heading (h2|h3).
 */
$vr_args    = wp_parse_args(
	$args ?? array(),
	array(
		'show_media'   => true,
		'show_excerpt' => true,
		'heading'      => 'h3',
	)
);
$vr_cat     = vr_primary_category();
$vr_heading = in_array( $vr_args['heading'], array( 'h2', 'h3' ), true ) ? $vr_args['heading'] : 'h3';
?>
<article class="card">
	<?php if ( $vr_args['show_media'] ) : ?>
		<a class="card-media<?php echo has_post_thumbnail() ? '' : ' is-empty'; ?>" href="<?php the_permalink(); ?>" tabindex="-1" aria-hidden="true">
			<?php
			if ( has_post_thumbnail() ) {
				the_post_thumbnail( 'vr-card', array( 'loading' => 'lazy', 'alt' => '' ) );
			} else {
				echo '<span>' . esc_html( vr_initial( get_the_title() ) ) . '</span>';
			}
			?>
		</a>
	<?php endif; ?>
	<?php if ( $vr_cat ) : ?>
		<a class="kicker" href="<?php echo esc_url( get_term_link( $vr_cat ) ); ?>"><?php echo esc_html( $vr_cat->name ); ?></a>
	<?php endif; ?>
	<<?php echo $vr_heading; // phpcs:ignore ?> class="card-title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></<?php echo $vr_heading; // phpcs:ignore ?>>
	<?php if ( $vr_args['show_excerpt'] ) : ?>
		<p class="card-excerpt"><?php echo esc_html( get_the_excerpt() ); ?></p>
	<?php endif; ?>
	<p class="meta">
		<time datetime="<?php echo esc_attr( get_the_modified_date( DATE_W3C ) ); ?>"><?php echo esc_html( vr_was_updated() ? 'Mis à jour le ' . get_the_modified_date( 'j F Y' ) : get_the_date( 'j F Y' ) ); ?></time>
		· <?php echo (int) vr_reading_time(); ?> min
	</p>
</article>
