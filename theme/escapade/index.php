<?php
/**
 * Gabarit de secours (WordPress l'exige). Les vrais gabarits sont home.php, archive.php, single.php, page.php.
 */
get_header();
?>
<div class="wrap">
	<header class="archive-head"><h1><?php echo esc_html( wp_strip_all_tags( get_the_archive_title() ) ); ?></h1></header>
	<div class="grid">
		<?php
		while ( have_posts() ) :
			the_post();
			get_template_part( 'template-parts/card' );
		endwhile;
		?>
	</div>
	<?php get_template_part( 'template-parts/pagination' ); ?>
</div>
<?php
get_footer();
