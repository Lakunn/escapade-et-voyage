</main>
<footer class="site-footer">
	<div class="wrap">
		<div class="footer-grid">
			<div class="footer-brand">
				<p class="brand-name"><?php echo esc_html( vr_config( 'brand.name', get_bloginfo( 'name' ) ) ); ?></p>
				<p><?php echo esc_html( vr_config( 'footer.about', '' ) ); ?></p>
			</div>
			<div>
				<h2>Rubriques</h2>
				<ul>
				<?php
				foreach ( (array) vr_config( 'categories', array() ) as $vr_cat ) :
					$vr_term = get_category_by_slug( $vr_cat['slug'] ?? '' );
					if ( ! $vr_term ) {
						continue;
					}
					?>
					<li><a href="<?php echo esc_url( get_term_link( $vr_term ) ); ?>"><?php echo esc_html( $vr_term->name ); ?></a></li>
				<?php endforeach; ?>
				</ul>
			</div>
			<div>
				<h2>Le média</h2>
				<?php vr_nav( 'footer_nav' ); ?>
			</div>
		</div>
		<div class="footer-bottom">
			<span>© <?php echo esc_html( wp_date( 'Y' ) ); ?> <?php echo esc_html( vr_config( 'author.name', 'Valentin Rouault' ) ); ?>. <?php echo esc_html( vr_config( 'footer.legal', '' ) ); ?></span>
			<span><?php if ( vr_config( 'analytics' ) ) : ?><a href="#" data-consent-open>Gérer les cookies</a> · <?php endif; ?><a href="<?php echo esc_url( home_url( '/llms.txt' ) ); ?>">llms.txt</a> · <a href="<?php echo esc_url( get_bloginfo( 'rss2_url' ) ); ?>">RSS</a></span>
		</div>
	</div>
</footer>
<?php wp_footer(); ?>
</body>
</html>
