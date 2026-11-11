<?php
/**
 * Page des articles (/blog-seo/), paginée : /blog-seo/page/N/.
 */
get_header();
$vr_blog_id = (int) get_option( 'page_for_posts' );
?>
<div class="wrap">
	<header class="archive-head">
		<span class="kicker">Tous les articles</span>
		<h1><?php echo esc_html( $vr_blog_id ? get_the_title( $vr_blog_id ) : 'Articles' ); ?></h1>
		<?php
		if ( $vr_blog_id ) {
			$vr_intro = get_post_field( 'post_content', $vr_blog_id );
			if ( $vr_intro ) {
				echo '<div class="prose">' . wp_kses_post( wpautop( $vr_intro ) ) . '</div>';
			}
		}
		?>
		<nav class="cat-pills" aria-label="Rubriques">
			<?php
			foreach ( (array) vr_config( 'categories', array() ) as $vr_conf ) :
				$vr_term = get_category_by_slug( $vr_conf['slug'] ?? '' );
				if ( $vr_term && $vr_term->count ) :
					?>
				<a href="<?php echo esc_url( get_term_link( $vr_term ) ); ?>"><?php echo esc_html( $vr_term->name ); ?></a>
					<?php
				endif;
			endforeach;
			?>
		</nav>
	</header>
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
