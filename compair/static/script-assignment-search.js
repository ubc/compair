let api_url = "/api/assignment/search/enddate";

const options = { year: 'numeric', month: 'short', day: 'numeric' };
let localeLang = 'en-ca';
var searchDay = new Date().toLocaleDateString(localeLang, options);

const d = new Date();
let diff = d.getTimezoneOffset();
let localTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

function formatDateYYMMDD(date) {
    var d = new Date(date),
        month = '' + (d.getMonth() + 1),
        day = '' + d.getDate(),
        year = d.getFullYear();

    if (month.length < 2)
        month = '0' + month;
    if (day.length < 2)
        day = '0' + day;

    return [year, month, day].join('-');
}

function formatDate(date) {
    if (date.includes("Invalid Date")){
        return searchDay;
    }
    var d = (new Date(date.toString().replace(/-/g, '\/')) );
    return d.toLocaleDateString(localeLang, options);
}

function getObjectDate(object)
{
    searchDay = formatDate(object);
    if (object.includes("Invalid Date")){
        searchDay = new Date().toLocaleDateString(localeLang, options);
    }
    strURL = api_url.concat('?compare_end=').concat(formatDateYYMMDD(searchDay)).concat('&compare_localTimeZone=').concat(localTimeZone.toString());

    getsearchapi(strURL);
}
// Defining async function
async function getsearchapi(url) {

    // Storing response
    const response = await fetch(url);

    // Storing data in form of JSON
    var search_data = await response.json();
    //console.log(search_data);
    if (response) {
        hideloadersearch();
    }
    showsearchapi(search_data);
}

// Function to hide the loader
function hideloadersearch() {
    document.getElementById('loading').style.display = 'none';
}
// Function to define innerHTML for HTML table
function showsearchapi(search_data) {

    let tab = `<tr>
          <th>Course Name</th>
          <th>Assignment Name</th>
          <th>Answering Begins</th>
          <th>Answering Ends</th>
          <th>Comparing Begins</th>
          <th>Comparing Ends</th>
         </tr>`;


    var iKey = 0;
    for (let key in  search_data) {
        let obj = JSON.parse(search_data[key])

        if (obj.compare_start == null){
            obj.compare_start = 'After answering ends';
        }

        if (obj.compare_end == null){
            obj.compare_end = '<i>No end date</i>';
        }
        //FOR NEXT RELEASE 2 DISPLAY SELF_EVAL_DATES
        //tab += `<tr><td>${JSON.stringify(obj.course_name).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.name).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.answer_start).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.answer_end).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.compare_start).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.compare_end).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.self_eval_end).replace(/\"/g, "")}</td></tr>`;
        tab += `<tr><td>${JSON.stringify(obj.course_name).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.name).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.answer_start).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.answer_end).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.compare_start).replace(/\"/g, "")}</td><td>${JSON.stringify(obj.compare_end).replace(/\"/g, "")}</td></tr>`;
        iKey++;
    }

    var iKeyText = iKey.toString() + " active assignments";
    if (iKey ==1){
        iKeyText = iKey.toString() + " active assignment";
    }
    document.getElementById("searchDay").innerHTML = (searchDay);
    document.getElementById("numberOfAssignment").innerHTML = iKeyText;

    // Setting innerHTML as tab variable
    document.getElementById("apiresults").innerHTML = tab;
}

getsearchapi(api_url);
