use libxml::xpath;
use libxml::parser::Parser;
use libxml::tree::document::Document;

use std::fs::File;
use std::io::Read;

struct XDocument {
    document: Document,
    context: xpath::Context,
}

impl XDocument {
    fn new(parser: Parser, ml: &str) -> Self {

        let doc = parser.parse_string(&ml)
            .expect("Bad parse");

        let ctx = xpath::Context::new(&doc)
            .expect("Bad context");

        XDocument {
            document: doc,
            context: ctx,
        }
    }
}

fn main() {

    let mut file = File::open("./data/rust.html")
        .expect("Bad file");
    let mut contents = String::new();

    file.read_to_string(&mut contents)
        .expect("Bad read");

    let parser = Parser::default_html();
    let mut doc = XDocument::new(parser, &contents);

    let path = "//div[@id='links']/div/div/h2[@class='result__title']";
    let results = doc.context.findnodes(path, None)
        .expect("bad xpath search");

    println!("{} results", results.len());
    for node in results {
        println!("\t{}", node.get_content());
        if node.is_text_node() {
            println!("\t\tis a text node");
        }
    }
}

