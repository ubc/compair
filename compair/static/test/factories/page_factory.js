function PageFactory() {}

PageFactory.prototype.createPage = function(pageName) {
    var page = undefined;
    try {
        page = require('../page_objects/'+pageName.replace(/\s/g, '_'));
    } catch (e) {
        if (e.code == 'MODULE_NOT_FOUND') {
            e.message = 'Requested page "' + pageName + '" is not defined in page mapping!';
        }
        throw e;
    }

    return new page;
};

module.exports = PageFactory;