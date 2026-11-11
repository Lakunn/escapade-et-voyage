<?php
get_header();
?>
<div class="wrap">
	<header class="archive-head">
		<span class="kicker">Erreur 404</span>
		<h1>Cette page n'existe pas (ou plus).</h1>
		<p>Lance une recherche ou reviens aux derniers articles.</p>
		<p style="margin-top:1.2rem"><?php get_search_form(); ?></p>
	</header>
	<div class="grid">
		<?php
		$vr_latest = new WP_Query(
			array(
				'posts_per_page' => 6,
				'no_found_rows'  => true,
			)
		);
		while ( $vr_latest->have_posts() ) :
			$vr_latest->the_post();
			get_template_part( 'template-parts/card' );
		endwhile;
		wp_reset_postdata();
		?>
	</div>
</div>
<?php
get_footer();
