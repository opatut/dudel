$ ->
    $field = $('#create-type-field')
    $list  = $('#create-type-list')

    setListCurrent = (key) ->
        $list.find('li').removeClass('current')
        $list.find('li[data-key="' + key + '"]').addClass('current')

    $field.change ->
        setListCurrent($field.val())

    $list.find('li').click ->
        key = $(this).attr('data-key')
        setListCurrent(key)
        $field.val(key)

    setListCurrent($field.val())


    # ---------------------------------------------------


    $("#advanced-toggle").click ->
        $("#advanced-closed").toggleClass("hidden")
        $("#advanced-open").toggleClass("hidden")
        $("#advanced-open").hide().fadeIn() # bit of effect
        false
