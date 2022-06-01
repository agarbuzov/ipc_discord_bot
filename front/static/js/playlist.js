let counter = 1

$('.add').on('click', function () {
    counter += 1
    $('#new_chq').append(
        `<div class="input-group mb-3" id="new_${counter}">
            <span class="input-group-text">${counter}</span>
            <input type="text" class="form-control" placeholder="https://www.youtube.com/...">
        </div>`
    )
})

$('.remove').on('click', function () {
    if (counter > 1) {
        $('#new_' + counter).remove()
        counter -= 1
    }
})

$('#inputImageFile').on('change', function (e) {
    let output = $('#filePreview')
    let url = URL.createObjectURL(e.target.files[0])
    output.attr('src', url)
    output.on('load', function () {
        URL.revokeObjectURL(url)
    })
})
