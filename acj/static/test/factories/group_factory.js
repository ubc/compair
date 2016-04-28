function GroupFactory() {};

GroupFactory.prototype.generateGroup = function (id, name) {
    var newGroup = {
        id: id,
        name: name
    };
    
    return newGroup;
};

module.exports = GroupFactory;
