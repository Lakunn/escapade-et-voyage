<?php
/**
 * Article : rubrique, titre, chapô, signature datée, « L'essentiel », sommaire, bio, articles liés.
 */
get_header();
while ( have_posts() ) :
	the_post();
	$vr_cat       = vr_primary_category();
	$vr_essentiel = vr_essentiel();
	$vr_has_toc   = vr_toc_h2_count() >= 3;
	?>
<article <?php post_class( 'wrap' ); ?>>
	<header class="article-head">
		<?php if ( $vr_cat ) : ?>
			<a class="kicker" href="<?php echo esc_url( get_term_link( $vr_cat ) ); ?>"><?php echo esc_html( $vr_cat->name ); ?></a>
		<?php endif; ?>
		<h1><?php the_title(); ?></h1>
		<?php if ( has_excerpt() ) : ?>
			<p class="dek"><?php echo esc_html( get_the_excerpt() ); ?></p>
		<?php endif; ?>
		<div class="byline">
			<span>Par <a class="author" href="<?php echo esc_url( home_url( (string) vr_config( 'author.page', '/' ) ) ); ?>" rel="author"><?php echo esc_html( vr_config( 'author.name', get_the_author() ) ); ?></a></span>
			<span>Publié le <time datetime="<?php echo esc_attr( get_the_date( DATE_W3C ) ); ?>"><?php echo esc_html( get_the_date( 'j F Y' ) ); ?></time></span>
			<?php if ( vr_was_updated() ) : ?>
				<span class="updated">Mis à jour le <time datetime="<?php echo esc_attr( get_the_modified_date( DATE_W3C ) ); ?>"><?php echo esc_html( get_the_modified_date( 'j F Y' ) ); ?></time></span>
			<?php endif; ?>
			<span><?php echo (int) vr_reading_time(); ?> min de lecture</span>
		</div>
	</header>

	<?php if ( has_post_thumbnail() ) : ?>
		<figure class="article-cover"><?php the_post_thumbnail( 'vr-cover', array( 'fetchpriority' => 'high', 'loading' => 'eager' ) ); ?></figure>
	<?php endif; ?>

	<div class="article-layout<?php echo $vr_has_toc ? '' : ' no-toc'; ?>">
		<div>
			<?php
			$gc_health = array_intersect( wp_list_pluck( get_the_category(), 'slug' ), (array) vr_config( 'urgence_categories', array( 'sante', 'premiers-secours' ) ) );
			if ( $gc_health && vr_config( 'urgence.texte' ) ) :
				?>
				<aside class="urgence" role="note"><strong>Urgence :</strong> <?php echo esc_html( vr_config( 'urgence.texte' ) ); ?></aside>
			<?php endif; ?>
			<?php if ( $vr_essentiel ) : ?>
				<section class="essentiel" aria-labelledby="essentiel-title">
					<h2 id="essentiel-title">L'essentiel</h2>
					<ul>
						<?php foreach ( $vr_essentiel as $vr_point ) : ?>
							<li><?php echo wp_kses( $vr_point, array( 'strong' => array(), 'em' => array(), 'sup' => array(), 'sub' => array(), 'a' => array( 'href' => array() ) ) ); ?></li>
						<?php endforeach; ?>
					</ul>
				</section>
			<?php endif; ?>
			<div class="prose">
				<?php the_content(); ?>
			</div>
			<?php get_template_part( 'template-parts/author-box' ); ?>
		</div>
		<?php if ( $vr_has_toc ) : ?>
			<aside class="toc-aside"><?php vr_toc(); ?></aside>
		<?php endif; ?>
	</div>
</article>

	<?php
	if ( $vr_cat ) :
		$vr_related = new WP_Query(
			array(
				'cat'                 => $vr_cat->term_id,
				'posts_per_page'      => 3,
				'post__not_in'        => array( get_the_ID() ),
				'ignore_sticky_posts' => true,
				'no_found_rows'       => true,
			)
		);
		if ( $vr_related->have_posts() ) :
			?>
<section class="wrap related" aria-labelledby="related-title">
	<h2 id="related-title">À lire aussi dans « <?php echo esc_html( $vr_cat->name ); ?> »</h2>
	<div class="grid">
			<?php
			while ( $vr_related->have_posts() ) :
				$vr_related->the_post();
				get_template_part( 'template-parts/card' );
			endwhile;
			wp_reset_postdata();
			?>
	</div>
</section>
			<?php
		endif;
	endif;
	?>
<div class="wrap"><?php get_template_part( 'template-parts/newsletter' ); ?></div>
	<?php
endwhile;
get_footer();
