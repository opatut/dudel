function get_slug(s) {
    s = s.replace(/[\s+]+/g, '-');
    s = s.replace(/[^a-zA-Z0-9_-]+/g, '');
    s = s.replace(/-+/g, '-');
    s = s.toLowerCase();
    return s;
}

$(document).ready(function() {
    $("[data-slug-field]").on("input", function() {
        var val = $(this).val();
        var slug = get_slug(val);
        var slug_input = $($(this).attr("data-slug-field"));
        slug_input.val(slug);
    });
});
