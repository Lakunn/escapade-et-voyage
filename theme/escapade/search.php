<?php
get_header();
?>
<div class="wrap">
	<header class="archive-head">
		<span class="kicker">Recherche</span>
		<h1>Résultats pour « <?php echo esc_html( get_search_query() ); ?> »</h1>
		<?php get_search_form(); ?>
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
		<p>Aucun résultat. Essaie un autre terme, ou parcours les rubriques.</p>
	<?php endif; ?>
</div>
<?php
get_footer();
