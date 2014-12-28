showComment = ->
    $(this).hide().closest("td").find("input")
        .css("width", 0).show()
        .animate({
            width: "100%"
        }, 400, "easeOutQuart");
    return false

setChoiceByCell = (cell) ->
    setChoice($(cell).parents("tr").data("vote-choice"), $(cell).data("choice"));

resetChoiceByCell = (cell) ->
    setChoice($(cell).parents("tr").data("vote-choice"), 0);

setChoice = (voteChoice, choice) ->
    $tr = $ "[data-vote-choice=\"#{voteChoice}\"]"
    $tr.find("input[type=\"radio\"]").prop "checked", false
    $tr.find("input[type=\"radio\"][value=\"#{choice}\"]").prop "checked", true
    $tr.find("td.vote-choice").addClass "off"
    $tr.find("td.vote-choice[data-choice=\"#{choice}\"]").removeClass "off"

$ ->
    # Hide voting radio column
    $("td .vote-choice-radio").parent().hide()

    # Apply checked radio states to table cells
    $(".vote-choice-radio:checked").each ->
        val = $(this).val()
        $(this).closest("tr").find("[data-choice=\"#{val}\"]").removeClass("off");

    # Buttons: "Show comment field"
    $(".vote-choice-edit").click showComment

    # Button: "Show all comment fields"
    $(".vote-choice-edit-all").click ->
        $(".vote-choice-edit").each (i) ->
            setTimeout =>
                showComment.call $(@)
            , i * 50

    # Hide comment fields, but show those that do have input
    $(".vote-comment .vote-choice-comment").hide()

    $(".vote-comment input[value!=\"\"]").each ->
        showComment.call($(this).closest(".vote-comment").find(".vote-choice-edit"))

    # Button: "all" (selecting the whole column)
    $(".vote-choice-column").click ->
        choice = $(this).data("choice")
        $('.vote-choice[data-choice="' + choice + '"]').each ->
            setChoiceByCell this

    # Fast selecting of voting cells
    draggingMouse = false
    draggingStartCell = null

    $("td.vote-choice").mousedown ->
        draggingMouse = true
        draggingStartCell = this
        $('table.vote').disableSelect()

        # set starting choice
        if $(this).hasClass "off"
            setChoiceByCell this
        else
            resetChoiceByCell this

        $('body').on 'mouseup', ->
            draggingMouse = false
            $('table.vote').enableSelect()

    $("td.vote-choice").mouseenter ->
        # set starting choice
        if draggingMouse
            if draggingStartCell
                setChoiceByCell draggingStartCell
                draggingStartCell = null

            setChoiceByCell this

    $(".vote-choice-radio").change ->
        setChoice($(this).parents("tr").data("vote-choice"), $(this).val())

