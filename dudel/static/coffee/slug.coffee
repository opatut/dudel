makeRandomString = (length) ->
    text = ""
    possible = "ABCDEFGHJKLMNPQRTUVWXYZabcdefghjkmnpqrstuvwxyz0123456789"

    for i in [0...length]
        text += possible.charAt(Math.floor(Math.random() * possible.length))

    return text

$ ->
    $randomize       = $ '#slug-randomize'
    $title           = $ '#title-input'
    $slug            = $ '#slug-input'
    $customizeBox    = $ '#slug-customize'
    $preview         = $ '#slug-preview'
    $previewBox      = $ '#slug-preview-box'
    $customizeButton = $ '#slug-customize-button'

    # Check if we are on a page with a slug input
    return if $title.length == 0

    update = (random) ->
        title     = $title.val()

        if RANDOM_SLUGS or random or not title
            slug = makeRandomString 8
        else
            slug = get_slug title

        $slug.val slug
        $preview.text slug

        if title
            $previewBox.parent().removeClass("initial-hidden")
        else
            $previewBox.parent().addClass("initial-hidden")

    updateTitle = ->
        update(false)
        return false

    updateRandom = ->
        update(true)
        return false

    openCustomize = ->
        $previewBox.hide().removeClass("script-only")
        $customizeBox.show()
        return false

    # Bind events
    $customizeButton.on "click", openCustomize
    $randomize.on       "click", updateRandom
    $title.on           "input", updateTitle
    update(false)

    # Hide the customization box, if there was no error
    $customizeBox.hide()
    if $customizeBox.find(".alert-danger").length > 0
        openCustomize()
