<?php
/**
 * Pages : guides piliers (avec sommaire si ≥ 3 H2), à propos, contact…
 */
get_header();
while ( have_posts() ) :
	the_post();
	$vr_hub       = vr_hub_children();
	$vr_has_toc   = ! $vr_hub && vr_toc_h2_count() >= 3;
	$vr_essentiel = vr_essentiel();
	?>
<article <?php post_class( 'wrap' ); ?>>
	<header class="page-head">
		<?php if ( $vr_has_toc ) : ?><span class="kicker">Guide de référence</span><?php endif; ?>
		<h1><?php the_title(); ?></h1>
		<?php if ( has_excerpt() ) : ?>
			<p class="dek"><?php echo esc_html( get_the_excerpt() ); ?></p>
		<?php endif; ?>
		<?php if ( $vr_has_toc ) : ?>
		<div class="byline">
			<span>Par <a class="author" href="<?php echo esc_url( home_url( (string) vr_config( 'author.page', '/' ) ) ); ?>" rel="author"><?php echo esc_html( vr_config( 'author.name' ) ); ?></a></span>
			<span class="updated">Mis à jour le <time datetime="<?php echo esc_attr( get_the_modified_date( DATE_W3C ) ); ?>"><?php echo esc_html( get_the_modified_date( 'j F Y' ) ); ?></time></span>
			<span><?php echo (int) vr_reading_time(); ?> min de lecture</span>
		</div>
		<?php endif; ?>
	</header>
	<?php vr_hub_cards( $vr_hub ); ?>
	<div class="article-layout<?php echo $vr_has_toc ? '' : ' no-toc'; ?>">
		<div>
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
			<div class="prose"><?php the_content(); ?></div>
			<?php
			if ( $vr_has_toc ) {
				get_template_part( 'template-parts/author-box' );
			}
			?>
		</div>
		<?php if ( $vr_has_toc ) : ?>
			<aside class="toc-aside"><?php vr_toc(); ?></aside>
		<?php endif; ?>
	</div>
</article>
	<?php
endwhile;
get_footer();
