$ ->
    $("[data-toggle-class]").click (e) ->
        target = $(this).data("target")
        $target = if target then $(target) else $(this)

        classname = $(this).data("toggle-class")

        $target.toggleClass(classname)

        e.preventDefault()

    Mousetrap.bind 'escape', ->
        $("#poll-container").removeClass("fullscreen")

    Mousetrap.bind 'f', ->
        console.log 'triggereds'
        $("#poll-container").toggleClass("fullscreen")

