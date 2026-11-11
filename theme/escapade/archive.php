<?php
/**
 * Rubriques (/category/…/), auteur (/author/…/) et autres archives.
 */
get_header();
$vr_term = is_category() ? get_queried_object() : null;
$vr_conf = $vr_term ? vr_category_config( $vr_term->slug ) : array();
?>
<div class="wrap">
	<header class="archive-head">
		<span class="kicker"><?php echo is_category() ? 'Rubrique' : ( is_author() ? 'Auteur' : 'Archives' ); ?></span>
		<h1><?php echo esc_html( is_author() ? vr_config( 'author.name', get_the_author() ) : wp_strip_all_tags( single_term_title( '', false ) ? single_term_title( '', false ) : get_the_archive_title() ) ); ?></h1>
		<?php
		if ( is_author() ) {
			echo '<p>' . esc_html( vr_config( 'author.bio', '' ) ) . '</p>';
		} elseif ( ! empty( $vr_conf['intro'] ) ) {
			echo '<p>' . esc_html( $vr_conf['intro'] ) . '</p>';
		} elseif ( term_description() ) {
			echo wp_kses_post( term_description() );
		}
		?>
		<?php if ( is_category() ) : ?>
		<nav class="cat-pills" aria-label="Rubriques">
			<?php
			foreach ( (array) vr_config( 'categories', array() ) as $vr_c ) :
				$vr_t = get_category_by_slug( $vr_c['slug'] ?? '' );
				if ( $vr_t && $vr_t->count ) :
					?>
				<a class="<?php echo $vr_t->term_id === $vr_term->term_id ? 'is-active' : ''; ?>" href="<?php echo esc_url( get_term_link( $vr_t ) ); ?>"><?php echo esc_html( $vr_t->name ); ?></a>
					<?php
				endif;
			endforeach;
			?>
		</nav>
		<?php endif; ?>
	</header>
	<?php if ( have_posts() ) : ?>
	<div class="grid">
		<?php
		while ( have_posts() ) :
			the_post();
			get_template_part( 'template-parts/card' );
		endwhile;
		?>
	</div>
		<?php get_template_part( 'template-parts/pagination' ); ?>
	<?php else : ?>
		<p>Aucun article pour le moment.</p>
	<?php endif; ?>
</div>
<?php
get_footer();
