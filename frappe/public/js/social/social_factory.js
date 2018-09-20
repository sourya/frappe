frappe.views.socialFactory = class socialFactory extends frappe.views.Factory {
	show() {
		this.make('social');
	}

	make(page_name) {
		const assets = [
			'/assets/js/social.min.js'
		];

		frappe.require(assets, () => {
			frappe.social.wall = new frappe.social.Wall({
				parent: this.make_page(true, page_name)
			});
		});
	}
};

$(document).on('toolbar_setup', () => {
	$('#toolbar-user .navbar-reload').after(`
		<li>
			<a class="social-link" href="#social/home">${__('Social')}
		</li>
	`);
});