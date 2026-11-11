<?php
/**
 * Accueil du média : à la une, manifeste (contenu de la page d'accueil), rubriques, newsletter.
 */
// Accueil paginé (/page/2/…) quand l'accueil liste les articles : gabarit de liste classique.
if ( is_paged() ) {
	require get_template_directory() . '/home.php';
	return;
}

get_header();

$vr_seen = array();
$vr_lead = new WP_Query(
	array(
		'posts_per_page'      => 5,
		'ignore_sticky_posts' => false,
		'no_found_rows'       => true,
	)
);
?>
<div class="wrap">
	<h1 class="screen-reader-text"><?php echo esc_html( vr_config( 'home.h1', vr_config( 'brand.name' ) ) ); ?></h1>

	<?php if ( $vr_lead->have_posts() ) : ?>
	<section class="lead" aria-label="À la une">
		<div class="lead-main">
			<?php
			$vr_lead->the_post();
			$vr_seen[] = get_the_ID();
			get_template_part( 'template-parts/card', null, array( 'heading' => 'h2' ) );
			?>
		</div>
		<div class="lead-side">
			<h2 class="side-title">Aussi à lire</h2>
			<?php
			while ( $vr_lead->have_posts() ) :
				$vr_lead->the_post();
				$vr_seen[] = get_the_ID();
				get_template_part(
					'template-parts/card',
					null,
					array(
						'show_media'   => false,
						'show_excerpt' => false,
					)
				);
			endwhile;
			?>
		</div>
	</section>
		<?php
		wp_reset_postdata();
	endif;
	?>

	<?php
	// Manifeste : contenu de la page définie comme page d'accueil (content/pages/accueil.md).
	if ( have_posts() ) :
		while ( have_posts() ) :
			the_post();
			if ( '' !== trim( get_the_content() ) ) :
				?>
	<section class="manifesto">
		<h2><?php echo esc_html( vr_config( 'home.manifesto_title', 'Le média' ) ); ?></h2>
		<div class="prose"><?php the_content(); ?></div>
	</section>
				<?php
			endif;
		endwhile;
	endif;
	?>

	<?php
	foreach ( (array) vr_config( 'categories', array() ) as $vr_conf ) :
		if ( empty( $vr_conf['on_home'] ) ) {
			continue;
		}
		$vr_term = get_category_by_slug( $vr_conf['slug'] );
		if ( ! $vr_term ) {
			continue;
		}
		$vr_q = new WP_Query(
			array(
				'cat'                 => $vr_term->term_id,
				'posts_per_page'      => 3,
				'post__not_in'        => $vr_seen,
				'ignore_sticky_posts' => true,
				'no_found_rows'       => true,
			)
		);
		if ( ! $vr_q->have_posts() ) {
			continue;
		}
		?>
	<section class="section" aria-labelledby="sec-<?php echo esc_attr( $vr_term->slug ); ?>">
		<div class="section-head">
			<div>
				<h2 id="sec-<?php echo esc_attr( $vr_term->slug ); ?>"><?php echo esc_html( $vr_term->name ); ?></h2>
				<?php if ( ! empty( $vr_conf['tagline'] ) ) : ?>
					<p><?php echo esc_html( $vr_conf['tagline'] ); ?></p>
				<?php endif; ?>
			</div>
			<a class="more" href="<?php echo esc_url( get_term_link( $vr_term ) ); ?>">Toute la rubrique →</a>
		</div>
		<div class="grid">
			<?php
			while ( $vr_q->have_posts() ) :
				$vr_q->the_post();
				$vr_seen[] = get_the_ID();
				get_template_part( 'template-parts/card' );
			endwhile;
			wp_reset_postdata();
			?>
		</div>
	</section>
	<?php endforeach; ?>

	<?php get_template_part( 'template-parts/newsletter' ); ?>
</div>
<?php
get_footer();
