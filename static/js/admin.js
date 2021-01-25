function openFirstForm() {
    var tabcontent;
    var navitem;
    tabcontent = document.getElementsByClassName("tabcontent");
    navitem = document.getElementsByClassName("nav-item");

    tabcontent[0].style.display = "block";
    navitem[0].className += " active";
}

function openForm(evt, cityName) {
    var i, tabcontent, navitem;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    navitem = document.getElementsByClassName("nav-item");
    for (i = 0; i < navitem.length; i++) {
        navitem[i].className = navitem[i].className.replace(" active", "");
    }
    document.getElementById(cityName).style.display = "block";
    evt.currentTarget.className += " active";
}

function changeChaine(idTab) {
    //get selected site value
    var site = document.getElementById(idTab + "-site").value;
    selectChaine = document.getElementById(idTab + "-chaine");
    //hide every choice except the empty one
    for (i = 1; i < selectChaine.options.length; i++) {
        selectChaine.options[i].style.display = "none";
    }
    //display the chaine choices according to site. For example, when site A is selected, chaine options with name A will be displayed
    document.getElementsByName(idTab + site).forEach(element => element.style.display = "block");
    //change the selected option to the first empty one
    selectChaine.options[0].selected = 'selected'
}